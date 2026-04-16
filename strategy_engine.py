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

def get_trading_signal(ticker, target_vol=0.15):
    try:
        df = yf.download(ticker, period="1y", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if 'Adj Close' not in df.columns:
            df['Adj Close'] = df['Close']
        
        # 指標計算
        df['SMA_5'] = df['Adj Close'].rolling(5).mean()
        df['SMA_20'] = df['Adj Close'].rolling(20).mean()
        df['SMA_60'] = df['Adj Close'].rolling(60).mean()
        ema12 = df['Adj Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Adj Close'].ewm(span=26, adjust=False).mean()
        df['MACD_Hist'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
        df['yz_vol'] = calculate_yz_volatility(df)
        df['mom_score'] = (df['Adj Close'].pct_change(20) > 0).astype(int) + (df['Adj Close'].pct_change(60) > 0).astype(int)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        return {
            "price": latest['Adj Close'], "open": latest['Open'],
            "volume": latest['Volume'], "prev_volume": prev['Volume'],
            "volatility": latest['yz_vol'], "mom_score": latest['mom_score'],
            "suggested_pos": min((target_vol / max(latest['yz_vol'], 0.05)) * (latest['mom_score'] / 2), 1.2),
            "history": df
        }
    except Exception as e:
        return None
