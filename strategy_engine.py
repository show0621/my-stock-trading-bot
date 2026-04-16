import yfinance as yf
import pandas as pd
import numpy as np

def get_expert_report(ticker_name):
    """資深分析師產業動態庫 - 2026.04.16 更新"""
    # 建立產業情資映射
    insights = {
        "半導體": {
            "題材": "2奈米產線良率超預期，AI ASIC 專案 4 月進入量產。CoWoS 產能與先進散熱需求爆發。",
            "法說": "台積電法說公告毛利率 66.2% 創高。魏哲家強調 AI 需求將進入為期 5 年的結構性增長。",
            "看多": 72, "分布": "左偏強勢分布"
        },
        "代工伺服器": {
            "題材": "GB200/GB300 整機出貨 4 月量產。液冷技術滲透率從 10% 跳升至 35%。",
            "法說": "廣達/鴻海維持 AI 業務翻倍成長目標。法人看好毛利率受惠產品組合優化轉強。",
            "看多": 65, "分布": "寬廣趨勢分布"
        },
        "金融": {
            "題材": "台股均量 5000 億支撐經紀收入。海外債券部位評價利益隨利率穩定回升。",
            "法說": "2026 盈餘分配率預計調升。殖利率估算達 4.5% - 5.2%，避險資金鎖定。",
            "看多": 55, "分布": "常態防禦分布"
        }
    }
    
    # 根據名稱分類
    if any(x in ticker_name for x in ["台積電", "聯發科", "日月光", "世芯", "聯電"]):
        cat = "半導體"
    elif any(x in ticker_name for x in ["鴻海", "廣達", "緯穎", "緯創", "技嘉"]):
        cat = "代工伺服器"
    elif any(x in ticker_name for x in ["金", "保"]):
        cat = "金融"
    else:
        cat = None

    info = insights.get(cat, {
        "題材": "權值股表現穩健，受全球 AI 資本支出擴大趨勢支撐。",
        "法說": "展望維持正向。法人籌碼呈現區間換手，具備高殖利率護體。",
        "看多": 50, "分布": "低波動震盪分布"
    })
    return info

def get_trading_signal(ticker, ticker_name, initial_cap=200000):
    df = yf.download(ticker, period="1y", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # 指標運算
    df['SMA5'], df['SMA20'] = df['Close'].rolling(5).mean(), df['Close'].rolling(20).mean()
    ema12, ema26 = df['Close'].ewm(span=12).mean(), df['Close'].ewm(span=26).mean()
    df['MACD_Hist'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9).mean()
    
    # 雙向回測
    balance, in_pos, buy_price, entry_idx, pos_type = initial_cap, False, 0, 0, ""
    trades = []

    for i in range(30, len(df)):
        row, date_str = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
        if not in_pos:
            if row['Close'] > row['SMA20'] and row['MACD_Hist'] > 0:
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Long"
                trades.append({"日期": date_str, "動作": "▲ 做多", "價格": round(buy_price, 1), "餘額": int(balance), "分析": f"【技術面】站上月線且動能轉強。"})
            elif row['Close'] < row['SMA20'] and row['MACD_Hist'] < 0:
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Short"
                trades.append({"日期": date_str, "動作": "▼ 放空", "價格": round(buy_price, 1), "餘額": int(balance), "分析": f"【趨勢】破月線轉弱，空頭動能增強。"})
        elif in_pos:
            days = i - entry_idx
            p_pct = (row['Close'] - buy_price)/buy_price if pos_type == "Long" else (buy_price - row['Close'])/buy_price
            if p_pct >= 0.06 or p_pct <= -0.03 or days >= 7:
                balance += p_pct * initial_cap * 2
                trades.append({"日期": date_str, "動作": "◆ 平倉", "價格": round(row['Close'], 1), "餘額": int(balance), "分析": f"結算損益：{int(p_pct*initial_cap*2):+} 元。"})
                in_pos = False

    return {
        "history": df, 
        "ledger": trades[::-1], 
        "equity": int(balance), 
        "report": get_expert_report(ticker_name)
    }
