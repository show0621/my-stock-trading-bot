import os
import json
import time
import yfinance as yf
import pandas as pd
import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY")

def find_working_model():
    """自動尋找目前帳號支援且可用的 Flash 模型 ID"""
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # 優先找包含 'flash' 的模型，且避開已被標註為過時的模型
                if 'flash' in m.name.lower() and 'experimental' not in m.name.lower():
                    # 回傳格式如 'models/gemini-1.5-flash'
                    return m.name
        return 'models/gemini-1.5-flash' # 預設回傳
    except Exception as e:
        print(f"無法列出模型: {e}")
        return 'models/gemini-1.5-flash'

def main():
    if not API_KEY:
        print("Error: Missing GEMINI_API_KEY")
        return

    genai.configure(api_key=API_KEY)
    
    # 自動獲取正確的模型 ID，解決 404 問題
    target_model = find_working_model()
    print(f"使用模型: {target_model}")
    model = genai.GenerativeModel(target_model)

    # 讀取清單
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
            # 配合免費配額，每 12 秒執行一次
            time.sleep(12)
            
        except Exception as e:
            print(f"{sym} 略過: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("分析完成。")

if __name__ == "__main__":
    main()
