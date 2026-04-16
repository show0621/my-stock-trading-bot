import yfinance as yf
import pandas as pd
import numpy as np
import os

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
        sigma_sq = v_o + k * v_c + (1 - k) * v_rs
        return np.sqrt(sigma_sq * 252)
    except:
        return pd.Series(0.18, index=df.index)

def get_trading_signal(ticker, target_vol=0.15):
    df = yf.download(ticker, period="1y", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if 'Adj Close' not in df.columns:
        df['Adj Close'] = df['Close']
    
    # 內建指標計算 (SMA, MACD)
    df['SMA_20'] = df['Adj Close'].rolling(20).mean()
    df['SMA_60'] = df['Adj Close'].rolling(60).mean()
    ema12 = df['Adj Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Adj Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Sig'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Sig']
    
    df['yz_vol'] = calculate_yz_volatility(df)
    df['mom_score'] = (df['Adj Close'].pct_change(20) > 0).astype(int) + (df['Adj Close'].pct_change(60) > 0).astype(int)
    
    latest = df.iloc[-1]
    vol = max(latest['yz_vol'], 0.05)
    pos_size = (target_vol / vol) * (latest['mom_score'] / 2)
    
    return {
        "price": latest['Adj Close'],
        "volatility": latest['yz_vol'],
        "mom_score": latest['mom_score'],
        "suggested_pos": min(pos_size, 1.2),
        "history": df,
        "volume": latest['Volume'],
        "open": latest['Open']
    }
