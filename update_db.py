import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai
import json
import time
import os

# 🔐 安全讀取 API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TOP_N_STOCKS = 30 # 每天精選前 30 檔最強動能股進行 AI 深度分析

def load_stock_universe():
    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return ["2330.TW", "2317.TW", "2454.TW", "2382.TW", "1582.TW"]

def quant_screener(tickers):
    print(f"🔍 啟動全市場掃描 (共 {len(tickers)} 檔)...")
    try:
        # 批量下載最近三個月數據
        data = yf.download(tickers, period="3mo", group_by="ticker", progress=False)
    except: return []
    
    results = []
    if len(tickers) == 1: data = {tickers[0]: data}
    
    for ticker in tickers:
        try:
            df = data[ticker].dropna() if len(tickers) > 1 else data.dropna()
            if len(df) < 20: continue
            
            # 1. 流動性過濾 (近 5 日均量 > 2000 張)
            vol_ma5 = df['Volume'].rolling(5).mean().iloc[-1]
            if vol_ma5 < 2000 * 1000: continue 
            
            # 2. 強勢動能評分
            s20 = 1 if df['Close'].iloc[-1] > df['Close'].iloc[-20] else -1
            pc = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]
            
            results.append({
                "symbol": ticker, 
                "score": s20 + abs(pc)*10, 
                "last_row": df.iloc[-1], 
                "vol_ma5": vol_ma5
            })
        except: pass
    
    return sorted(results, key=lambda x: x["score"], reverse=True)[:TOP_N_STOCKS]

def main():
    if not GEMINI_API_KEY:
        print("❌ 找不到 API Key")
        return
        
    top_stocks = quant_screener(load_stock_universe())
    # 建立資料庫架構
    db = {"MARKET_SUMMARY": {"top_picks": [s["symbol"] for s in top_stocks], "update_time": time.strftime("%Y-%m-%d %H:%M:%S")}}
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3-flash') # 使用穩定的 flash 模型

    for s in top_stocks:
        sym = s["symbol"]
        print(f"🔄 AI 正在撰寫分析報告: {sym}...")
        try:
            tkr = yf.Ticker(sym)
            # 計算籌碼特徵
            r, v = s["last_row"], s["vol_ma5"]
            p_c = (r['Close']-r['Open'])/r['Open']
            chip = "外資進攻盤" if p_c > 0.03 else "法人觀望盤"
            
            ctx = f"公司:{sym}\n籌碼:{chip}\n最新新聞:{str([n.get('title') for n in tkr.news[:3]])}"
            prompt = f"你是外資投研部主管。針對資料:{ctx} 給出深度解析。利多利空結尾必加(觸及率:XX%)。嚴格輸出JSON:{{利多,利空,展望,利基,題材,機率:{{多,空,盤}}}}"
            
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            db[sym] = {
                "name": tkr.info.get("shortName", sym),
                "report": json.loads(response.text),
                "chip_type": chip,
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            time.sleep(5) # 尊重大大頻率限制
        except Exception as e:
            print(f"❌ {sym} 分析失敗: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("✅ 全台股精選報告更新完畢！")

if __name__ == "__main__":
    main()
