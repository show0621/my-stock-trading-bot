import yfinance as yf
import pandas as pd
import google.generativeai as genai # 👈 回歸最穩定的導入路徑
import json
import time
import os

# 1. 拿鑰匙
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def load_stock_universe():
    try:
        # 讀取你的 all_tw_stocks.txt
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return ["2330.TW", "2317.TW", "2454.TW", "1582.TW"]

def main():
    if not GEMINI_API_KEY:
        print("❌ 找不到 API Key，請檢查 Secrets 設定")
        return
    
    # 2. 設定 AI (Gemini 3 Flash)
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3-flash') 
    
    tickers = load_stock_universe()
    db = {"MARKET_SUMMARY": {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}}
    
    # 測試階段我們先跑前 5 檔，確保穩穩過關
    for sym in tickers[:5]:
        print(f"🔄 正在為孟霖分析: {sym}...")
        try:
            tkr = yf.Ticker(sym)
            news = [n.get('title') for n in tkr.news[:3]]
            prompt = f"你是台股專家，請針對 {sym} 的新聞 {news} 給出利多、利空、展望，並以 JSON 格式輸出。"
            
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            db[sym] = {
                "name": tkr.info.get("shortName", sym),
                "report": json.loads(response.text),
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            time.sleep(3) # 慢慢跑，比較快
        except Exception as e:
            print(f"⚠️ {sym} 略過: {e}")

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("✅ 分析任務圓滿完成！")

if __name__ == "__main__":
    main()
