# 檔案名稱：update_db.py (請在本地電腦執行)
import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai
import json
import time
import os

# 🔑 請在這裡直接貼上你的 Gemini API Key
GEMINI_API_KEY = "AIzaSy你的Gemini密碼放這裡"

# 你的核心追蹤清單
STOCK_LIST = {
    "2330.TW": "台積電", "2454.TW": "聯發科", "3711.TW": "日月光",
    "2317.TW": "鴻海", "2382.TW": "廣達", "6669.TW": "緯穎",
    "2881.TW": "富邦金", "2891.TW": "中信金", "1582.TW": "信錦"
}

def get_chip_sentiment(r, v_ma):
    v_r = r['Volume'] / v_ma if v_ma > 0 else 1
    p_c = (r['Close'] - r['Open']) / r['Open']
    b_r = abs(r['Close'] - r['Open']) / (r['High'] - r['Low'] + 0.001)
    if v_r > 2.5 and abs(p_c) < 0.02: return "高檔換手盤 (Hand-over)"
    if p_c > 0.03 and b_r > 0.7: return "外資進攻盤 (Foreign-Led)"
    if 0 < p_c < 0.02 and 1.2 < v_r < 2.0: return "投信養券盤 (IT-Led)"
    if v_r > 1.8 and b_r < 0.3: return "散戶浮額盤 (Retail-Led)"
    return "法人觀望盤 (Neutral)"

def generate_report(sym, nm):
    print(f"🔄 正在深度分析: {nm} ({sym})...")
    try:
        tkr = yf.Ticker(sym)
        df = tkr.history(period="1mo")
        v_ma = df['Volume'].rolling(5).mean().iloc[-2]
        chip = get_chip_sentiment(df.iloc[-1], v_ma)
        
        news = tkr.news
        info = tkr.info
        
        ctx = f"公司:{nm}({sym})\n籌碼現況:{chip}\n新聞:{str([n.get('title') for n in news[:5]])}"
        prompt = f"你是外資策略師。資料:{ctx}\n請根據籌碼與新聞進行深度解析。利多利空結尾必須加(觸及率:XX%)。嚴格輸出JSON包含:利多,利空,展望,利基,題材,機率(多,空,盤總和100)"
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        res = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json") # 強制穩定輸出 JSON
        )
        return json.loads(res.text), chip
    except Exception as e:
        print(f"❌ {nm} 分析失敗: {e}")
        return {"利多":"資料庫更新失敗","利空":"-","展望":"-","利基":"-","題材":"-","機率":{"多":33,"空":33,"盤":34}}, "未知"

def main():
    print("🚀 啟動 AI 首席投研造庫系統...")
    database = {}
    for sym, nm in STOCK_LIST.items():
        report, chip = generate_report(sym, nm)
        database[sym] = {"report": report, "chip_type": chip, "update_time": time.strftime("%Y-%m-%d %H:%M:%S")}
        time.sleep(5) # 休息 5 秒，完美避開流量限制
        
    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=4)
    print("✅ 所有股票分析完畢！已儲存至 ai_database.json")

if __name__ == "__main__":
    main()
