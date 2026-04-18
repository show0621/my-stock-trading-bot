import os
import time

def main():
    print("✅ [系統通訊測試] Python 引擎已成功啟動！")
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        print("🔑 API Key 偵測狀態：已就緒")
    else:
        print("❌ API Key 偵測狀態：未設定 (請檢查 Secrets)")
    
    # 建立一個測試用的空資料庫，證明機器人有寫入權限
    import json
    test_data = {"test": "success", "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open("ai_database.json", "w") as f:
        json.dump(test_data, f)
    print("💾 測試資料庫已寫入。")

if __name__ == "__main__":
    main()
