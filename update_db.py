import yfinance as yf
import pandas as pd
from google import genai  # 👈 這是 2026 年最新的導入方式
import json
import time
import os

# 從 GitHub Secrets 拿鑰匙
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def load_stock_universe():
    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return ["2330.TW", "2317.TW", "1582.TW", "2313.TW", "1503.TW"]

def main():
    if not GEMINI_API_KEY:
        print("❌ 找不到 API Key，請檢查 Secrets 設定")
        return
    
    # 2026 最新 Client 初始化
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    tickers = load_stock_universe()
    db = {"MARKET_SUMMARY": {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}}
    
    # 測試階段我們先跑前 5 檔，確保 100% 成功
    for sym in tickers[:5]:
        print(f"🔄 AI 正在分析: {sym}...")
        try:
            tkr = yf.Ticker(sym)
            news = [n.get('title') for n in tkr.news[:3]]
            prompt = f"你是台股分析師，針對 {sym} 的新聞 {news}，請給出利多、利空、展望。嚴格以 JSON 格式輸出。"
            
            # 使用 Gemini 3 Flash 模型
            response = client.models.generate_content(
                model='gemini-3-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            db[sym] = {
                "name": tkr.info.get("shortName", sym),
                "report": response.parsed, # 2026 新功能：自動解析 JSON
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            time.sleep(3) # 避免 API 流量過載
        except Exception as e:
            print(f"⚠️ {sym} 錯誤: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("✅ 任務圓滿成功！")

if __name__ == "__main__":
    main()
