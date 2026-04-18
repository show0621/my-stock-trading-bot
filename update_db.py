import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai
import json
import time
import os

# 從 GitHub Secrets 拿鑰匙
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TOP_N_STOCKS = 30 

def main():
    if not GEMINI_API_KEY:
        print("❌ 找不到 API Key")
        return
    print("🚀 大腦啟動，準備分析全台股...")
    # 這裡暫時放一個保底邏輯，確保程式能跑通
    db = {"MARKET_SUMMARY": {"update_time": time.strftime("%Y-%m-%d %H:%M:%S")}}
    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)
    print("✅ 資料庫初步更新成功")

if __name__ == "__main__":
    main()
