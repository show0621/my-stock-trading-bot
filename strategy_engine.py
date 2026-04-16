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
    except: return pd.Series(0.18, index=df.index)

def get_trading_signal(ticker, target_vol=0.15, initial_cap=200000):
    df = yf.download(ticker, period="1y", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # 指標：SMA5, SMA20, SMA60
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA60'] = df['Close'].rolling(60).mean()
    df['yz_vol'] = calculate_yz_volatility(df)
    
    # 策略：動能分數 (放寬：只要站上20MA就有1分)
    df['mom_score'] = (df['Close'] > df['SMA20']).astype(int) + (df['Close'] > df['SMA60']).astype(int)
    
    # --- 全年回測引擎 ---
    balance = initial_cap
    equity_curve = []
    trades = []
    in_pos = False
    buy_price = 0
    lots = 0
    
    for i in range(60, len(df)):
        row = df.iloc[i]
        date_str = df.index[i].strftime('%Y/%m/%d')
        
        # 波動率調節口數計算
        pos_ratio = (target_vol / max(row['yz_vol'], 0.05)) * (row['mom_score'] / 2)
        current_margin = row['Close'] * 100 * 0.135
        calc_lots = int((balance * pos_ratio) / current_margin) if current_margin > 0 else 0
        
        # 買入訊號
        if row['mom_score'] >= 1 and not in_pos and calc_lots > 0:
            in_pos = True
            buy_price = row['Close']
            lots = calc_lots
            trades.append({"日期": date_str, "動作": "▲ 買入", "價格": round(buy_price,1), "口數": lots, "損益": "-"})
        
        # 賣出訊號
        elif row['mom_score'] == 0 and in_pos:
            pnl = (row['Close'] - buy_price) * 100 * lots - 100 # 扣除手續費
            balance += pnl
            in_pos = False
            trades.append({"日期": date_str, "動作": "▼ 賣出", "價格": round(row['Close'],1), "口數": lots, "損益": int(pnl)})
            
        equity_curve.append(balance + ((row['Close'] - buy_price) * 100 * lots if in_pos else 0))

    return {
        "price": df.iloc[-1]['Close'], "volatility": df.iloc[-1]['yz_vol'],
        "mom_score": df.iloc[-1]['mom_score'], "history": df,
        "ledger": trades[::-1], "equity": int(balance),
        "curve": equity_curve, "roi": round(((balance/initial_cap)-1)*100, 2)
    }
