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
        return pd.Series(0.16, index=df.index)

def get_trading_signal(ticker, target_vol=0.15):
    df = yf.download(ticker, period="1y", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 手寫指標計算
    df['SMA_5'] = df['Close'].rolling(5).mean()
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_60'] = df['Close'].rolling(60).mean()
    df['Vol_MA5'] = df['Volume'].rolling(5).mean()
    
    df['yz_vol'] = calculate_yz_volatility(df)
    df['mom_score'] = (df['Close'].pct_change(20) > 0).astype(int) + (df['Close'].pct_change(60) > 0).astype(int)
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    return {
        "price": latest['Close'],
        "open": latest['Open'],
        "volume": latest['Volume'],
        "prev_volume": prev['Volume'],
        "volatility": latest['yz_vol'],
        "mom_score": latest['mom_score'],
        "suggested_pos": min((target_vol / max(latest['yz_vol'], 0.05)) * (latest['mom_score'] / 2), 1.2),
        "history": df
    }
