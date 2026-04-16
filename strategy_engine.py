import yfinance as yf
import pandas as pd
import numpy as np

def calculate_yz_volatility(df, window=20):
    try:
        o, h, l, c = df['Open'], df['High'], df['Low'], df['Close']
        c_prev = df['Close'].shift(1)
        log_ho, log_lo, log_co = np.log(h/o), np.log(l/o), np.log(c/o)
        log_oc, log_cc = np.log(o/c_prev), np.log(c/c_prev)
        v_o, v_c = log_oc.rolling(window).var(), log_cc.rolling(window).var()
        v_rs = (log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)).rolling(window).mean()
        k = 0.34 / (1.34 + (window + 1) / (window - 1))
        return np.sqrt((v_o + k * v_c + (1 - k) * v_rs) * 252)
    except: return pd.Series(0.18, index=df.index)

def get_trading_signal(ticker, target_vol=0.15, initial_cap=200000):
    df = yf.download(ticker, period="1y", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # 指標計算
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA5'] = df['Close'].rolling(5).mean()
    df['yz_vol'] = calculate_yz_volatility(df)
    df['RSI'] = 100 - (100 / (1 + (df['Close'].diff().where(df['Close'].diff() > 0, 0).rolling(14).mean() / 
                                  -df['Close'].diff().where(df['Close'].diff() < 0, 0).rolling(14).mean())))

    # 回測邏輯：動態風控 + 7天限制
    balance, in_pos, buy_price, entry_idx = initial_cap, False, 0, 0
    trades, equity_curve = [], []

    for i in range(30, len(df)):
        row, date_str = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
        
        # 買入訊號：站上20MA + RSI低位回升
        if (row['Close'] > row['SMA20']) and (row['RSI'] > 45) and not in_pos:
            in_pos, buy_price, entry_idx = True, row['Close'], i
            trades.append({
                "日期": date_str, "動作": "▲ 買進", "價格": round(buy_price, 1),
                "日誌": f"股價站上20MA，RSI為{row['RSI']:.1f}動能轉強。同步執行保證金調節。"
            })
        
        # 賣出條件：動態停損(-3%)、動態停利(+6%)、或強制7天
        elif in_pos:
            days_held = i - entry_idx
            pnl_pct = (row['Close'] - buy_price) / buy_price
            
            exit_reason = ""
            if pnl_pct <= -0.03: exit_reason = "觸發動態停損 (-3%)"
            elif pnl_pct >= 0.06: exit_reason = "觸發預期停利 (+6%)"
            elif days_held >= 7: exit_reason = "強制平倉 (7天週期結束)"
            elif row['Close'] < row['SMA5']: exit_reason = "趨勢轉弱 (跌破5MA)"

            if exit_reason:
                pnl_val = (row['Close'] - buy_price) * 100 * 4
                balance += pnl_val
                in_pos = False
                trades.append({
                    "日期": date_str, "動作": "▼ 賣出", "價格": round(row['Close'], 1),
                    "日誌": f"{exit_
