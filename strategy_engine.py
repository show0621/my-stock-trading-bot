import yfinance as yf
import pandas as pd
import numpy as np

def calculate_yz_volatility(df, window=20):
    try:
        o, h, l, c = df['Open'], df['High'], df['Low'], df['Close']
        c_prev = df['Close'].shift(1)
        log_ho, log_lo, log_co = np.log(h/o), np.log(l/o), np.log(c/o)
        log_oc, log_cc = np.log(o/c_prev), np.log(c/c_prev)
        v_o = log_oc.rolling(window=window).var()
        v_c = log_cc.rolling(window=window).var()
        v_rs = (log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)).rolling(window=window).mean()
        k = 0.34 / (1.34 + (window + 1) / (window - 1))
        return np.sqrt((v_o + k * v_c + (1 - k) * v_rs) * 252)
    except:
        return pd.Series(0.18, index=df.index)

def get_trading_signal(ticker, target_vol=0.15, initial_cap=200000):
    df = yf.download(ticker, period="1y", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # 指標計算
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA5'] = df['Close'].rolling(5).mean()
    df['yz_vol'] = calculate_yz_volatility(df)
    diff = df['Close'].diff()
    up, down = diff.where(diff > 0, 0).rolling(14).mean(), -diff.where(diff < 0, 0).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (up/down)))
    ema12, ema26 = df['Close'].ewm(span=12, adjust=False).mean(), df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_Hist'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()

    # --- 雙向回測引擎 ---
    balance, in_pos, buy_price, entry_idx = initial_cap, False, 0, 0
    pos_type = "" # "Long" 或 "Short"
    trades, equity_curve = [], []

    for i in range(30, len(df)):
        row, date_str = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
        
        if not in_pos:
            # 買入條件 (做多)
            if (row['Close'] > row['SMA20']) and (row['MACD_Hist'] > 0) and (row['RSI'] < 65):
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Long"
                trades.append({"日期": date_str, "動作": "▲ 做多", "價格": round(buy_price, 1), "日誌": f"站上20MA+MACD轉正。"})
            # 賣出條件 (放空)
            elif (row['Close'] < row['SMA20']) and (row['MACD_Hist'] < 0) and (row['RSI'] > 35):
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Short"
                trades.append({"日期": date_str, "動作": "▼ 放空", "價格": round(buy_price, 1), "日誌": f"跌破20MA+MACD轉負。"})
        
        elif in_pos:
            days = i - entry_idx
            pnl_pct = (row['Close'] - buy_price) / buy_price if pos_type == "Long" else (buy_price - row['Close']) / buy_price
            
            exit_reason = ""
            if pnl_pct >= 0.06: exit_reason = "預期停利(+6%)"
            elif pnl_pct <= -0.03: exit_reason = "動態停損(-3%)"
            elif days >= 7: exit_reason = "7天平倉"
            elif pos_type == "Long" and row['Close'] < row['SMA5']: exit_reason = "趨勢轉弱(破5MA)"
            elif pos_type == "Short" and row['Close'] > row['SMA5']: exit_reason = "空頭轉弱(站5MA)"

            if exit_reason:
                pnl_val = pnl_pct * initial_cap * 2 # 模擬2倍槓桿
                balance += pnl_val
                trades.append({"日期": date_str, "動作": "◆ 平倉", "價格": round(row['Close'], 1), "日誌": f"{exit_reason}。損益：{int(pnl_val)} 元。"})
                in_pos = False

        equity_curve.append(balance)

    return {"history": df, "ledger": trades[::-1], "equity": int(balance), "rsi": df.iloc[-1]['RSI'], "macd": df.iloc[-1]['MACD_Hist']}
