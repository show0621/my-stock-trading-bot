import os
import json
import time
import yfinance as yf
import pandas as pd
import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY")

def get_working_model():
    """動態尋找目前 API 支援的正確模型名稱"""
    try:
        models = [m.name for m in genai.list_models() 
                  if 'generateContent' in m.supported_generation_methods]
        # 優先尋找 1.5-flash 或 2.0-flash
        for target in ['flash']:
            for m in models:
                if target in m.lower():
                    return m
        return models[0] if models else "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

def main():
    if not API_KEY:
        print("Error: Missing API Key")
        return

    genai.configure(api_key=API_KEY)
    
    # 自動抓取模型 ID，解決 404 報錯
    model_id = get_working_model()
    print(f"正在使用模型: {model_id}")
    model = genai.GenerativeModel(model_id)

    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            tickers = [line.strip() for line in f if line.strip()][:10]
    except:
        tickers = ["2330.TW", "2317.TW"]

    db = {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}

    for sym in tickers:
        print(f"正在分析 {sym}...")
        try:
            tkr = yf.Ticker(sym)
            news = [n.get('title') for n in tkr.news[:3]]
            prompt = f"分析台股 {sym} 新聞: {news}。以 JSON 格式輸出：{{bullish, bearish, outlook}}"
            
            response = model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            
            db[sym] = {
                "name": tkr.info.get("shortName", sym),
                "report": json.loads(response.text)
            }
            # 延時確保符合免費配額 (每分鐘約 3-5 次請求)
            time.sleep(15)
            
        except Exception as e:
            print(f"{sym} 略過: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("分析任務結束。")

if __name__ == "__main__":
    main()
