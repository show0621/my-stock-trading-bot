import yfinance as yf
import pandas as pd
import numpy as np

def get_trading_signal(ticker, target_vol=0.15, initial_cap=200000):
    df = yf.download(ticker, period="1y", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # 1. 專業指標計算
    df['SMA5'] = df['Close'].rolling(5).mean()
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA60'] = df['Close'].rolling(60).mean()
    
    # MACD 手動計算
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_Line'] = ema12 - ema26
    df['MACD_Hist'] = df['MACD_Line'] - df['MACD_Line'].ewm(span=9, adjust=False).mean()
    
    # RSI 計算
    diff = df['Close'].diff()
    df['RSI'] = 100 - (100 / (1 + (diff.where(diff > 0, 0).rolling(14).mean() / -diff.where(diff < 0, 0).rolling(14).mean())))

    # 2. 型態學偵測：底底高 (Rising Lows) 與 收斂三角形 (Triangle)
    df['Low_Rising'] = (df['Low'] > df['Low'].shift(1)) & (df['Low'].shift(1) > df['Low'].shift(2))
    df['Range_10'] = df['High'].rolling(10).max() - df['Low'].rolling(10).min()
    df['Is_Converging'] = df['Range_10'] < df['Range_10'].shift(5)

    # --- 3. 雙向回測引擎 (含 7天鐵律與動態風控) ---
    balance, in_pos, buy_price, entry_idx = initial_cap, False, 0, 0
    pos_type, trades = "", []

    for i in range(30, len(df)):
        row, date_str = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
        prev = df.iloc[i-1]
        
        # 動態日誌文字
        p_desc = "三角形收斂突破" if row['Is_Converging'] else ("底底高上升型態" if row['Low_Rising'] else "區間盤整")
        v_desc = "法人縮量沈澱" if row['Volume'] < row['Volume'].rolling(5).mean().iloc[0] else "大戶帶量攻擊"

        if not in_pos:
            # 做多訊號
            if (row['Close'] > row['SMA20']) and (row['MACD_Hist'] > 0) and (row['RSI'] < 70):
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Long"
                trades.append({
                    "日期": date_str, "動作": "▲ 做多", "價格": round(buy_price, 1),
                    "詳細分析": f"【技術解析】站上月線且MACD轉正。【型態】呈現{p_desc}之攻擊姿態。【籌碼】{v_desc}。RSI位於{row['RSI']:.1f}，預期具備6%波段空間。"
                })
            # 放空訊號
            elif (row['Close'] < row['SMA20']) and (row['MACD_Hist'] < 0) and (row['RSI'] > 30):
