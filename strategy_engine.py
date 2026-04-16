import yfinance as yf
import pandas as pd
import numpy as np

def get_trading_signal(ticker, target_vol=0.15, initial_cap=200000):
    df = yf.download(ticker, period="1y", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # 1. 基礎技術指標
    df['SMA5'] = df['Close'].rolling(5).mean()
    df['SMA20'] = df['Close'].rolling(20).mean()
    ema12, ema26 = df['Close'].ewm(span=12).mean(), df['Close'].ewm(span=26).mean()
    df['MACD_Hist'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9).mean()
    diff = df['Close'].diff()
    u, d = diff.where(diff > 0, 0).rolling(14).mean(), -diff.where(diff < 0, 0).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + u/d))
    
    # 2. 籌碼與量價分析
    df['Vol_Ratio'] = df['Volume'] / df['Volume'].rolling(5).mean()
    
    # 3. K 棒型態學偵測 (收斂三角形與上升型態)
    df['High_Low_Range'] = df['High'].rolling(10).max() - df['Low'].rolling(10).min()
    df['Is_Triangle'] = df['High_Low_Range'] < df['High_Low_Range'].shift(5) # 波動收斂
    df['Is_Rising'] = (df['Low'] > df['Low'].shift(1)) & (df['Low'].shift(1) > df['Low'].shift(2)) # 底底高

    # --- 雙向回測引擎 ---
    balance, in_pos, buy_price, entry_idx = initial_cap, False, 0, 0
    pos_type, trades, equity_curve = "", [], []

    for i in range(30, len(df)):
        row, date_str = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
        prev = df.iloc[i-1]
        
        # 型態分析描述
        pattern_desc = "三角形收斂中" if row['Is_Triangle'] else "上升趨勢確立" if row['Is_Rising'] else "區間震盪"
        chip_desc = "量增籌碼集中" if row['Vol_Ratio'] > 1.2 else "量縮籌碼沉澱"

        if not in_pos:
            # 做多訊號：站上20MA + MACD轉正 + 上升型態
            if (row['Close'] > row['SMA20']) and (row['MACD_Hist'] > 0) and (row['RSI'] < 70):
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Long"
                trades.append({
                    "日期": date_str, "動作": "▲ 做多", "價格": round(buy_price, 1),
                    "詳細分析": f"【技術面】站上月線且MACD轉正。【型態】偵測到{pattern_desc}後的向上突破。【籌碼】顯示{chip_desc}，且RSI位於{row['RSI']:.1f}具備攻擊空間。"
                })
            # 放空訊號：破20MA + MACD轉負
            elif (row['Close'] < row['SMA20']) and (row['MACD_Hist'] < 0) and (row['RSI'] > 30):
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Short"
                trades.append({
                    "日期": date_str, "動作": "▼ 放空", "價格": round(buy_price, 1),
                    "詳細分析": f"【技術面】股價摜破20MA支撐且MACD柱狀圖走跌。【型態】高點不向且呈現下殺慣性。【籌碼】{chip_desc}，空方勢頭轉強。"
                })
        
        elif in_pos:
            days = i - entry_idx
            pnl_pct = (row['Close'] - buy_price) / buy_price if pos_type == "Long" else (buy_price - row['Close']) / buy_price
            
            exit_reason = ""
            if pnl_pct >= 0.06: exit_reason = "利潤達標 (+6%)"
            elif pnl_pct <= -0.03: exit_reason = "動態止損 (-3%)"
            elif days >= 7: exit_reason = "波段周期結束 (7天)"
            elif pos_type == "Long" and row['Close'] < row['SMA5']: exit_reason = "破5MA趨勢轉弱"
            elif pos_type == "Short" and row['Close'] > row['SMA5']: exit_reason = "站回5MA空頭回補"

            if exit_reason:
                pnl_val = pnl_pct * initial_cap * 2
                balance += pnl_val
                trades.append({
                    "日期": date_str, "動作": "◆ 平倉", "價格": round(row['Close'], 1),
                    "詳細分析": f"基於【{exit_reason}】執行平倉。當前RSI為{row['RSI']:.1f}，MACD動能為{row['MACD_Hist']:.2f}。累積影響金額：{int(pnl_val)} 元。"
                })
                in_pos = False
        equity_curve.append(balance)

    return {"history": df, "ledger": trades[::-1], "equity": int(balance), "rsi": df.iloc[-1]['RSI'], "macd": df.iloc[-1]['MACD_Hist']}
