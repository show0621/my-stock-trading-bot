import yfinance as yf
import pandas as pd
import numpy as np

def calculate_yz_volatility(df, window=20):
    """精確計算 Yang-Zhang 波動率 (考慮隔夜跳空)"""
    log_ho = np.log(df['High'] / df['Open'])
    log_lo = np.log(df['Low'] / df['Open'])
    log_co = np.log(df['Close'] / df['Open'])
    log_oc = np.log(df['Open'] / df['Close'].shift(1))
    log_cc = np.log(df['Close'] / df['Close'].shift(1))
    
    v_o = log_oc.rolling(window=window).var()
    v_c = log_cc.rolling(window=window).var()
    v_rs = (log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)).rolling(window=window).mean()
    
    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    sigma_sq = v_o + k * v_c + (1 - k) * v_rs
    return np.sqrt(sigma_sq * 252)

def get_trading_signal(ticker, target_vol=0.15):
    # 抓取台股數據 (還原股價)
    df = yf.download(ticker, period="1y")
    
    # 1. 計算動能因子 (20, 60, 120D)
    df['mom_score'] = (df['Adj Close'].pct_change(20) > 0).astype(int) + \
                      (df['Adj Close'].pct_change(60) > 0).astype(int)
    
    # 2. 計算 YZ 波動率
    df['yz_vol'] = calculate_yz_volatility(df)
    
    # 3. 部位調節邏輯 (Position Sizing)
    current_vol = df['yz_vol'].iloc[-1]
    mom_score = df['mom_score'].iloc[-1]
    # 建議持倉比 = (目標波動 / 當前波動) * (動能分數 / 2)
    pos_size = (target_vol / max(current_vol, 0.1)) * (mom_score / 2)
    
    return {
        "price": df['Adj Close'].iloc[-1],
        "volatility": current_vol,
        "mom_score": mom_score,
        "suggested_pos": min(pos_size, 1.2), # 最高 1.2 倍槓桿
        "history": df
    }
