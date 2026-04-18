import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai
import json
import time
import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TOP_N_STOCKS = 30 

def load_stock_universe(filepath="all_tw_stocks.txt"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return ["2330.TW", "2317.TW", "2454.TW", "2382.TW", "2881.TW", "2603.TW", "1582.TW", "3231.TW", "2303.TW", "3711.TW"]

def quant_screener(tickers):
    print(f"🔍 量化初篩中 (共 {len(tickers)} 檔)...")
    try:
        data = yf.download(tickers, period="3mo", group_by="ticker", progress=False)
    except: return []
    results = []
    if len(tickers) == 1: data = {tickers[0]: data}
    for ticker in tickers:
        try:
            df = data[ticker].dropna() if len(tickers) > 1 else data.dropna()
            if len(df) < 60: continue
            vol_ma5 = df['Volume'].rolling(5).mean().iloc[-1]
            if vol_ma5 < 2000 * 1000: continue
            s20 = 1 if df['Close'].iloc[-1] > df['Close'].iloc[-20] else -1
            s60 = 1 if df['Close'].iloc[-1] > df['Close'].iloc[-60] else -1
            conf = (s20 + s60) / 2
            pc = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]
            results.append({"symbol": ticker, "score": conf + abs(pc)*10, "last_row": df.iloc[-1], "vol_ma5": vol_ma5})
        except: pass
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:TOP_N_STOCKS]
    return results

def get_chip_sentiment(r, v_ma):
    v_r = r['Volume'] / v_ma if v_ma > 0 else 1
    p_c = (r['Close'] - r['Open']) / r['Open']
    b_r = abs(r['Close'] - r['Open']) / (r['High'] - r['Low'] + 0.001)
    if v_r > 2.5 and abs(p_c) < 0.02: return "高檔換手盤 (Hand-over)"
    if p_c > 0.03 and b_r > 0.7: return "外資進攻盤 (Foreign-Led)"
    if 0 < p_c < 0.02 and 1.2 < v_r < 2.0: return "投信養券盤 (IT-Led)"
    if v_r > 1.8 and b_r < 0.3: return "散戶浮額盤 (Retail-Led)"
    return "法人觀望盤 (Neutral)"

def generate_report(sym, chip):
    print(f"🔄 AI 深度分析: {sym}...")
    try:
        tkr = yf.Ticker(sym)
        ctx = f"公司:{sym}\n籌碼現況:{chip}\n新聞:{str([n.get('title') for n in tkr.news[:5]])}"
        prompt = f"你是外資策略師。資料:{ctx}\n請根據籌碼與新聞進行深度解析。利多利空結尾加(觸及率:XX%)。嚴格輸出JSON:{{利多,利空,展望,利基,題材,機率:{{多,空,盤}}}} 機率總和100"
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        res = model.generate_content(prompt, generation_config=genai.GenerationConfig(response_mime_type="application/json"))
        return json.loads(res.text), tkr.info.get("shortName", sym)
    except: return {"利多":"資料庫更新失敗","利空":"-","展望":"-","利基":"-","題材":"-","機率":{"多":33,"空":33,"盤":34}}, sym

def main():
    if not GEMINI_API_KEY: return
    top_stocks = quant_screener(load_stock_universe())
    database = {"MARKET_SUMMARY": {"top_picks": [s["symbol"] for s in top_stocks], "update_time": time.strftime("%Y-%m-%d %H:%M:%S")}}
    for s in top_stocks:
        sym, chip = s["symbol"], get_chip_sentiment(s["last_row"], s["vol_ma5"])
        rep, nm = generate_report(sym, chip)
        database[sym] = {"name": nm, "report": rep, "chip_type": chip, "update_time": time.strftime("%Y-%m-%d %H:%M:%S")}
        time.sleep(4)
    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
