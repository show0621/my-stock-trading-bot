import os
import json
import time
import yfinance as yf
import pandas as pd
import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY")

def main():
    if not API_KEY:
        print("Error: Missing API Key")
        return

    genai.configure(api_key=API_KEY)
    
    # 嘗試使用最穩定的模型名稱
    model_name = 'gemini-1.5-flash'
    try:
        # 測試模型是否存在，若 404 則嘗試加上 models/ 前綴
        model = genai.GenerativeModel(model_name)
        model.generate_content("test", generation_config={"max_output_tokens": 1})
    except Exception:
        model_name = 'models/gemini-1.5-flash'
        model = genai.GenerativeModel(model_name)

    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            tickers = [line.strip() for line in f if line.strip()][:10]
    except:
        tickers = ["2330.TW", "2317.TW"]

    db = {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}

    for sym in tickers:
        print(f"Analyzing {sym}...")
        try:
            tkr = yf.Ticker(sym)
            news = [n.get('title') for n in tkr.news[:3]]
            prompt = f"Analyze stock {sym} news: {news}. Output in JSON: {{bullish, bearish, outlook}}"
            
            response = model.generate_content(
                prompt, 
                generation_config={"response_mime_type": "application/json"}
            )
            
            db[sym] = {
                "name": tkr.info.get("shortName", sym),
                "report": json.loads(response.text)
            }
            # 延時以符合免費版配額
            time.sleep(12)
            
        except Exception as e:
            print(f"{sym} 略過: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("Done.")

if __name__ == "__main__":
    main()
