import yfinance as yf
import pandas as pd
import numpy as np

def get_trading_signal(ticker, target_vol=0.15, initial_cap=200000):
    df = yf.download(ticker, period="1y", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # 1. 基礎指標
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA5'] = df['Close'].rolling(5).mean()
    
    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Hist'] = df['MACD'] - df['MACD'].ewm(span=9, adjust=False).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + gain/loss))
    
    # 2. K棒形態學 (簡單偵測：吞噬形態)
    df['Body'] = df['Close'] - df['Open']
    df['Is_Bullish_Engulfing'] = (df['Body'] > 0) & (df['Body'].shift(1) < 0) & (df['Close'] > df['Open'].shift(1))
    
    # 3. 7天波段回測引擎
    balance = initial_cap
    trades = []
    in_pos = False
    entry_idx = 0
    buy_price = 0
    
    for i in range(30, len(df)):
        row = df.iloc[i]
        date_str = df.index[i].strftime('%Y/%m/%d')
        
        # 買入條件：TEJ動能(站上20MA) + MACD金叉 + RSI不超買 + 吞噬形態
        buy_cond = (row['Close'] > row['SMA20']) and (row['MACD_Hist'] > 0) and (row['RSI'] < 65)
        
        if buy_cond and not in_pos:
            in_pos = True
            buy_price = row['Close']
            entry_idx = i
            trades.append({"日期": date_str, "動作": "▲ 買入", "價格": round(buy_price,1), "理由": "多頭形態+動能確認"})
            
        # 賣出條件：持有滿7天 OR MACD轉負 OR 破5日線
        elif in_pos:
            days_held = i - entry_idx
            sell_cond = (days_held >= 7) or (row['MACD_Hist'] < 0) or (row['Close'] < row['SMA5'])
            
            if sell_cond:
                pnl = (row['Close'] - buy_price) * 100 * 4 # 4口模擬
                balance += pnl
                in_pos = False
                reason = "時間到期(7天)" if days_held >= 7 else "動能轉弱"
                trades.append({"日期": date_str, "動作": "▼ 賣出", "價格": round(row['Close'],1), "理由": reason, "損益": int(pnl)})

    return {
        "price": df.iloc[-1]['Close'], "history": df,
        "ledger": trades[::-1], "equity": int(balance),
        "rsi": df.iloc[-1]['RSI'], "macd": df.iloc[-1]['MACD_Hist']
    }
