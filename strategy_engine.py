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
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if 'Adj Close' not in df.columns:
        df['Adj Close'] = df['Close']
    
    # 指標計算
    df['SMA_20'] = df['Adj Close'].rolling(20).mean()
    df['SMA_60'] = df['Adj Close'].rolling(60).mean()
    ema12 = df['Adj Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Adj Close'].ewm(span=26, adjust=False).mean()
    df['MACD_Hist'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
    df['yz_vol'] = calculate_yz_volatility(df)
    df['mom_score'] = (df['Adj Close'].pct_change(20) > 0).astype(int) + (df['Adj Close'].pct_change(60) > 0).astype(int)
    
    # 建立虛擬帳本 (回測)
    trades = []
    equity = initial_cap
    in_position = False
    buy_price = 0
    
    for i in range(60, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # 買入訊號：動能轉強且尚未持倉
        if row['mom_score'] >= 1 and not in_position:
            in_position = True
            buy_price = row['Adj Close']
            trades.append({
                "日期": df.index[i].strftime('%Y/%m/%d'),
                "動作": "▲ 買入",
                "價格": round(buy_price, 1),
                "持倉比": f"{round((target_vol/max(row['yz_vol'],0.05))*50, 1)}%",
                "損益": 0
            })
        
        # 賣出訊號：動能轉弱且已持倉
        elif row['mom_score'] == 0 and in_position:
            pnl = (row['Adj Close'] - buy_price) * 100 * 4 # 以4口模擬
            equity += pnl
            in_position = False
            trades.append({
                "日期": df.index[i].strftime('%Y/%m/%d'),
                "動作": "▼ 賣出",
                "價格": round(row['Adj Close'], 1),
                "持倉比": "0%",
                "損益": int(pnl)
            })
            
    return {
        "price": df.iloc[-1]['Adj Close'],
        "volatility": df.iloc[-1]['yz_vol'],
        "mom_score": df.iloc[-1]['mom_score'],
        "history": df,
        "ledger": trades[::-1][:10], # 取最近10筆
        "equity": int(equity)
    }
