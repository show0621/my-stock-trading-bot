import os
import json
import time
import yfinance as yf
import pandas as pd
import numpy as np
from google import genai  # 2026 最新官方零件

# 1. 安全讀取環境變數
API_KEY = os.environ.get("GEMINI_API_KEY")

def get_tech_and_momentum(sym):
    """計算動能模型與 K 棒型態數據"""
    try:
        df = yf.download(sym, period="1mo", interval="1d", progress=False)
        if df.empty or len(df) < 20: return None
        
        # 動能計算 (Momentum Model)
        last_close = df['Close'].iloc[-1].item()
        prev_close = df['Close'].iloc[-2].item()
        week_ago_close = df['Close'].iloc[-5].item()
        
        roc_1d = ((last_close - prev_close) / prev_close) * 100
        roc_5d = ((last_close - week_ago_close) / week_ago_close) * 100
        
        # 成交量動能 (Volume Momentum)
        avg_vol = df['Volume'].rolling(5).mean().iloc[-1].item()
        last_vol = df['Volume'].iloc[-1].item()
        vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1
        
        # K 棒型態特徵 (K-line Patterns)
        high = df['High'].iloc[-1].item()
        low = df['Low'].iloc[-1].item()
        open_p = df['Open'].iloc[-1].item()
        
        upper_shadow = (high - max(open_p, last_close)) / (high - low) if (high - low) > 0 else 0
        lower_shadow = (min(open_p, last_close) - low) / (high - low) if (high - low) > 0 else 0
        body_size = abs(last_close - open_p) / (high - low) if (high - low) > 0 else 0
        
        return {
            "price": round(last_close, 2),
            "momentum": {
                "1d_change_pct": round(roc_1d, 2),
                "5d_change_pct": round(roc_5d, 2),
                "vol_spike_ratio": round(vol_ratio, 2)
            },
            "k_pattern": {
                "upper_shadow": round(upper_shadow, 2),
                "lower_shadow": round(lower_shadow, 2),
                "body_ratio": round(body_size, 2),
                "is_red": last_close > open_p
            }
        }
    except Exception as e:
        print(f"數據計算失敗 {sym}: {e}")
        return None

def main():
    if not API_KEY:
        print("Error: Missing API Key")
        return

    client = genai.Client(api_key=API_KEY)
    
    # 讀取股票清單
    try:
        with open("all_tw_stocks.txt", "r", encoding="utf-8") as f:
            tickers = [line.strip() for line in f if line.strip()][:15] # 考慮配額，先設 15 檔
    except:
        tickers = ["2330.TW", "2317.TW", "1582.TW", "2454.TW", "2382.TW"]

    db = {"update_time": time.strftime("%Y-%m-%d %H:%M:%S"), "stocks": {}}

    for sym in tickers:
        print(f"📊 正在進行全維度分析: {sym}...")
        tech_data = get_tech_and_momentum(sym)
        if not tech_data: continue

        try:
            tkr = yf.Ticker(sym)
            news = [n.get('title') for n in tkr.news[:3]]
            
            # 整合型提示詞 (System Framework)
            prompt = f"""
你現在是【頂級對沖基金首席策略師】。請整合以下數據進行全維度研判：

1.【技術面與動能模型】:
- 現價: {tech_data['price']}
- 5日漲跌幅: {tech_data['momentum']['5d_change_pct']}%
- 成交量增幅: {tech_data['momentum']['vol_spike_ratio']}倍 (大於1.5倍代表異常放量)
- K棒型態: 上影線比率 {tech_data['k_pattern']['upper_shadow']}, 下影線比率 {tech_data['k_pattern']['lower_shadow']}

2.【籌碼面預測】:
- 根據成交量異常與股價表現，推論「三大法人」(外資、投信、自營商) 的進出意圖。

3.【基本面新聞】:
- {news}

請綜合判斷後給出 JSON：
- analysis (趨勢診斷: 結合量價與K棒，說明目前是攻擊、回測還是出貨)
- chips_view (籌碼解讀: 法人可能的動作與目的)
- outlook (明日展望: 給出關鍵支撐壓力位與建議)
- signal (訊號: "強力買進", "偏多觀望", "減碼避險", "強烈空頭")
"""
            response = client.models.generate_content(
                model='gemini-3-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            db["stocks"][sym] = {
                "name": tkr.info.get("shortName", sym),
                "tech": tech_data,
                "report": response.parsed,
                "update_time": time.strftime("%H:%M:%S")
            }
            # 2026 免費版建議間隔 20 秒，避免 429 報錯
            time.sleep(20)
            
        except Exception as e:
            print(f"⚠️ {sym} 分析中斷: {e}")
            if "429" in str(e): break

    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("🚀 全方位分析報告已產出！")

if __name__ == "__main__":
    main()
