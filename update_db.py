import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai
import json
import time
import os

# 1. 從系統保險箱拿 API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TOP_N_STOCKS = 30 

def load_stock_universe():
    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return ["2330.TW", "2317.TW", "2454.TW", "2382.TW", "1582.TW"]

def quant_screener(tickers):
    print(f"🔍 掃描全市場 (共 {len(tickers)} 檔)...")
    try:
        data = yf.download(tickers, period="3mo", group_by="ticker", progress=False)
    except: return []
    res = []
    if len(tickers) == 1: data = {tickers[0]: data}
    for t in tickers:
        try:
            df = data[t].dropna()
            if len(df) < 20: continue
            vol = df['Volume'].rolling(5).mean().iloc[-1]
            if vol < 2000 * 1000: continue 
            conf = 1 if df['Close'].iloc[-1] > df['Close'].iloc[-20] else -1
            pc = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]
            res.append({"sym": t, "score": conf + abs(pc)*10, "row": df.iloc[-1], "vol": vol})
        except: pass
    return sorted(res, key=lambda x: x["score"], reverse=True)[:TOP_N_STOCKS]

def main():
    if not GEMINI_API_KEY:
        print("❌ 找不到 API KEY")
        return
    
    top_list = quant_screener(load_stock_universe())
    db = {"MARKET_SUMMARY": {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}}
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash') # 使用最新的穩定版
    
    for s in top_list:
        sym = s["sym"]
        print(f"分析中: {sym}...")
        try:
            tkr = yf.Ticker(sym)
            ctx = f"公司:{sym}\n新聞:{str([n.get('title') for n in tkr.news[:3]])}"
            prompt = f"你是外資分析師，針對{ctx}給出利多、利空、展望、利基。必須標註(觸及率:XX%)。輸出JSON格式。"
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            db[sym] = {"report": json.loads(response.text), "update_time": time.strftime("%Y-%m-%d %H:%M:%S")}
            time.sleep(5) # 避開流量限制
        except: pass
        
    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("✅ 資料庫更新成功")

if __name__ == "__main__":
    main()
