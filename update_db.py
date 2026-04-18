import os
import time
import json

def main():
    print("🚀 [大腦啟動成功] 這是真正的 Python 程式！")
    # 這裡先放一個最簡單的測試，確保流程能跑通
    result = {
        "status": "success",
        "msg": "AI 報告管線已打通",
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open("ai_database.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print("✅ 測試資料庫已存檔成功！")

if __name__ == "__main__":
    main()
