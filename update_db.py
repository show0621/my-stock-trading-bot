import os
import json
import time
import yfinance as yf
import pandas as pd
import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY")

def get_available_model(client_genai):
    """自動尋找可用的 Flash 模型，避免 404 錯誤"""
    try:
        for m in client_genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name.lower():
                    return m.name
        return 'gemini-1.5-flash' # 備用方案
    except:
        return 'gemini-1.5-flash'

def load_tickers():
    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return ["2330.TW", "2317.TW", "2454.TW"]

def main():
    if not API_KEY:
        print("Error: Missing GEMINI_API_KEY")
        return

    genai.configure(api_key=API_KEY)
    
    # 自動獲取當前環境支援的模型 ID
    model_id = get_available_model(genai)
    print(f"Using model: {model_id}")
    model = genai.GenerativeModel(model_id)

    tickers = load_tickers()
    db = {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}

    for sym in tickers[:10]:
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
                "report": json.loads(response.text),
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ {sym} 略過: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("Mission accomplished.")

if __name__ == "__main__":
    main()
