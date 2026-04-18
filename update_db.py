import os
import json
import time
import yfinance as yf
import pandas as pd
import google.generativeai as genai

# 從環境變數讀取 API Key
API_KEY = os.environ.get("GEMINI_API_KEY")

def load_tickers():
    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        # 若找不到檔案，則提供預設清單
        return ["2330.TW", "2317.TW", "2454.TW", "1582.TW", "2308.TW"]

def main():
    if not API_KEY:
        print("Error: Missing GEMINI_API_KEY")
        return

    # 初始化 Gemini
    genai.configure(api_key=API_KEY)
    
    # 修正模型名稱為穩定版本，解決 404 錯誤
    model = genai.GenerativeModel('gemini-1.5-flash')

    tickers = load_tickers()
    db = {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}

    # 測試執行前 10 檔
    for sym in tickers[:10]:
        print(f"Analyzing {sym}...")
        try:
            tkr = yf.Ticker(sym)
            news = [n.get('title') for n in tkr.news[:3]]
            
            # 建立 Prompt
            prompt = f"Analyze stock {sym} news: {news}. Output in JSON format with fields: bullish, bearish, outlook."
            
            response = model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            
            # 儲存結果
            db[sym] = {
                "name": tkr.info.get("shortName", sym),
                "report": json.loads(response.text),
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            # 避免觸發 API 頻率限制
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ {sym} 略過: {e}")

    # 寫入 JSON
    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("✅ 分析任務完成。")

if __name__ == "__main__":
    main()
