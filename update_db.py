import os
import json
import time
import yfinance as yf
import pandas as pd
import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY")

def main():
    if not API_KEY:
        print("❌ Error: Missing GEMINI_API_KEY in Secrets.")
        return

    genai.configure(api_key=API_KEY)
    
    # 模型嘗試清單：從新到舊，哪一個有配額就用哪一個
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.0-pro']
    model = None
    
    # 嘗試建立模型
    for m_name in models_to_try:
        try:
            temp_model = genai.GenerativeModel(m_name)
            # 測試一下是否有配額 (做一個極小的請求)
            temp_model.generate_content("Hi", generation_config={"max_output_tokens": 1})
            model = temp_model
            print(f"✅ 成功啟用模型: {m_name}")
            break
        except Exception as e:
            print(f"⚠️ 模型 {m_name} 無配額或不可用: {e}")

    if not model:
        print("❌ 失敗：你所有的 Gemini 模型配額皆為 0。請至 Google Cloud Console 連結帳單帳戶以激活免費配額。")
        return

    # 讀取股票清單 (建議先縮小範圍測試)
    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            tickers = [line.strip() for line in f if line.strip()][:5] # 先跑 5 檔
    except:
        tickers = ["2330.TW", "2317.TW", "1582.TW"]

    db = {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}

    for sym in tickers:
        print(f"正在分析 {sym}...")
        try:
            tkr = yf.Ticker(sym)
            news = [n.get('title') for n in tkr.news[:3]]
            prompt = f"分析台股 {sym} 新聞: {news}。請給出利多、利空、展望，嚴格以 JSON 格式輸出。"
            
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            db[sym] = {
                "name": tkr.info.get("shortName", sym),
                "report": json.loads(response.text)
            }
            time.sleep(10) # 👈 關鍵：將間隔拉長到 10 秒，避免觸發 429 頻率限制
        except Exception as e:
            print(f"⚠️ {sym} 略過: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("✅ 任務執行完畢。")

if __name__ == "__main__":
    main()
