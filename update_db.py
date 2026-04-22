import os
import json
import time
import yfinance as yf
import pandas as pd
import numpy as np
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")

def calculate_yz_vol(df, window=22):
    log_ho = np.log(df['High'] / df['Open'])
    log_lo = np.log(df['Low'] / df['Open'])
    log_co = np.log(df['Close'] / df['Open'])
    log_oc = np.log(df['Open'] / df['Close'].shift(1))
    log_cc = np.log(df['Close'] / df['Close'].shift(1))
    s_o = log_oc.tail(window).var()
    s_c = log_cc.tail(window).var()
    s_rs = (log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)).tail(window).mean()
    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    return np.sqrt(s_o + k * s_c + (1 - k) * s_rs) * np.sqrt(252)

def main():
    if not API_KEY: return
    client = genai.Client(api_key=API_KEY)
    # 你關注的 0050 核心標的
    tickers = ["2330.TW", "2317.TW", "1582.TW", "2454.TW", "2382.TW", "3231.TW", "2603.TW"]
    db = {"update_date": time.strftime("%Y-%m-%d"), "stocks": {}}

    for sym in tickers:
        try:
            tkr = yf.Ticker(sym)
            df = tkr.history(period="5y") # 抓取 5 年數據
            if df.empty or len(df) < 120: continue
            
            curr_p = round(df['Close'].iloc[-1], 2)
            # 趨勢投票 (20/60/120)
            score = ( (1 if curr_p > df['Close'].iloc[-21] else -1) + 
                      (1 if curr_p > df['Close'].iloc[-61] else -1) + 
                      (1 if curr_p > df['Close'].iloc[-121] else -1) ) / 3
            confidence = max(0, score)
            yz_vol = calculate_yz_vol(df)
            
            # 支撐壓力與風險
            support = round(df['Low'].tail(60).min(), 2)
            resistance = round(df['High'].tail(60).max(), 2)

            prompt = f"""
你現在是【資深投研主管】，標的 {sym}。
數據：現價 {curr_p}, 趨勢信心 {confidence}, YZ波動率 {yz_vol}, 支撐 {support}, 壓力 {resistance}。
請產出 JSON: 
1.industry_analysis, 2.web_touch_rate(0-100), 3.probability_dist(多/空/盤), 
4.thematic_catalyst, 5.conference_outlook, 6.pros_and_cons, 
7.signal(強力買進/偏多/空手), 8.scoring(0-100), 9.tech_struct, 10.chips_base
"""
            response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt, config={'response_mime_type': 'application/json'})
            
            db["stocks"][sym] = {
                "name": tkr.info.get('shortName', sym),
                "quant": {"price": curr_p, "yz_vol": round(yz_vol, 4), "confidence": round(confidence, 2), "support": support, "resistance": resistance, "weight": round(min(1.0, (0.30/yz_vol)*confidence), 2)},
                "report": response.parsed,
                "earnings": str(tkr.calendar.get('Earnings Date', ['N/A'])[0]) if tkr.calendar else "N/A",
                "time": time.strftime("%H:%M:%S")
            }
            time.sleep(10)
        except Exception as e: print(f"Error {sym}: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
