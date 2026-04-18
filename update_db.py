import yfinance as yf
import pandas as pd
from google import genai # 👈 這是 2026 年最新的導入方式
import json
import time
import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def load_stock_universe():
    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return ["2330.TW", "2317.TW", "1582.TW"]

def quant_screener(tickers):
    print(f"🔍 啟動全市場掃描 (共 {len(tickers)} 檔)...")
    try:
        data = yf.download(tickers, period="3mo", group_by="ticker", progress=False)
    except: return []
    results = []
    if len(tickers) == 1: data = {tickers[0]: data}
    for t in tickers:
        try:
            df = data[t].dropna()
            if len(df) < 20: continue
            # 選股條件：近 5 日均量 > 1000 張且近 5 日有波動
            vol = df['Volume'].rolling(5).mean().iloc[-1]
            if vol < 1000 * 1000: continue 
            pc = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]
            results.append({"symbol": t, "score": abs(pc), "last_row": df.iloc[-1]})
        except: pass
    # 挑選動能最強的前 30 檔
    return sorted(results, key=lambda x: x["score"], reverse=True)[:30]

def main():
    if not GEMINI_API_KEY:
        print("❌ 找不到 API Key")
        return
        
    top_stocks = quant_screener(load_stock_universe())
    db = {"MARKET_SUMMARY": {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}}
    
    # 2026 最新的 Client 啟動方式
    client = genai.Client(api_key=GEMINI_API_KEY)

    for s in top_stocks:
        sym = s["symbol"]
        print(f"🔄 AI 正在撰寫分析報告: {sym}...")
        try:
            tkr = yf.Ticker(sym)
            ctx = f"公司:{sym}\n新聞:{[n.get('title') for n in tkr.news[:3]]}"
            prompt = f"你是外資投研主管。針對{ctx}給出深度解析。利多利空結尾必加(觸及率:XX%)。嚴格輸出JSON:{{利多,利空,展望,機率:{{多,空,盤}}}}"
            
            # 使用 Gemini 3 Flash 的最新語法
            response = client.models.generate_content(
                model='gemini-3-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            db[sym] = {
                "name": tkr.info.get("shortName", sym),
                "report": response.parsed, # 新版可以直接解析 JSON，不用自己載入
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            time.sleep(3) # 57 檔股票分析，間隔 3 秒避免被 API 鎖住
        except Exception as e:
            print(f"❌ {sym} 分析失敗: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("✅ 全台股精選報告更新完畢！")

if __name__ == "__main__":
    main()
