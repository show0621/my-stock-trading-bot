import yfinance as yf
import pandas as pd
import google.generativeai as genai  # 使用最穩定的標準庫
import json
import time
import os

# 1. 讀取密鑰
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def load_stock_universe():
    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return ["2330.TW", "2317.TW", "2454.TW", "1582.TW"]

def main():
    if not GEMINI_API_KEY:
        print("❌ 找不到 API Key，請檢查 GitHub Secrets")
        return
    
    # 設定 AI
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3-flash') # 2026 最強模型
    
    tickers = load_stock_universe()
    print(f"🔍 正在掃描台股清單...")
    
    # 這裡我們先抓取前 10 檔做測試，確保速度與成功率
    db = {"MARKET_SUMMARY": {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}}
    
    for sym in tickers[:10]: 
        print(f"🔄 AI 正在分析: {sym}...")
        try:
            tkr = yf.Ticker(sym)
            news = [n.get('title') for n in tkr.news[:3]]
            prompt = f"你是台股專家，請分析 {sym} 的最新新聞：{news}。請給出利多、利空與展望。輸出格式為 JSON。"
            
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            db[sym] = {
                "name": tkr.info.get("shortName", sym),
                "report": json.loads(response.text),
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            time.sleep(2) # 避開頻率限制
        except Exception as e:
            print(f"⚠️ {sym} 略過: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("✅ 分析任務圓滿完成！")

if __name__ == "__main__":
    main()
