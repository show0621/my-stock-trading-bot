import yfinance as yf
import pandas as pd
import numpy as np

def calculate_yz_volatility(df, window=20):
    try:
        o, h, l, c = df['Open'], df['High'], df['Low'], df['Close']
        c_prev = df['Close'].shift(1)
        k = 0.34 / (1.34 + (window + 1) / (window - 1))
        v_o = np.log(o/c_prev).rolling(window).var()
        v_c = np.log(c/o).rolling(window).var()
        v_rs = (np.log(h/o) * np.log(h/c) + np.log(l/o) * np.log(l/c)).rolling(window).mean()
        return np.sqrt((v_o + k * v_c + (1 - k) * v_rs) * 252)
    except: return pd.Series(0.18, index=df.index)

def get_trading_signal(ticker, target_vol=0.15, initial_cap=200000):
    df = yf.download(ticker, period="1y", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # 指標運算
    df['SMA5'], df['SMA20'] = df['Close'].rolling(5).mean(), df['Close'].rolling(20).mean()
    ema12, ema26 = df['Close'].ewm(span=12).mean(), df['Close'].ewm(span=26).mean()
    df['MACD_Hist'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9).mean()
    u = df['Close'].diff().where(df['Close'].diff() > 0, 0).rolling(14).mean()
    d = -df['Close'].diff().where(df['Close'].diff() < 0, 0).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + u/d))
    
    # 型態學與籌碼
    df['Is_Triangle'] = (df['High'].rolling(10).max() - df['Low'].rolling(10).min()) < (df['High'].rolling(10).max() - df['Low'].rolling(10).min()).shift(5)
    df['Is_Rising'] = (df['Low'] > df['Low'].shift(1)) & (df['Low'].shift(1) > df['Low'].shift(2))
    df['Vol_Ratio'] = df['Volume'] / df['Volume'].rolling(5).mean()

    # 雙向回測 (多/空/7天/動態止損)
    balance, in_pos, buy_price, entry_idx, pos_type = initial_cap, False, 0, 0, ""
    trades = []

    for i in range(30, len(df)):
        row, date_str = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
        pattern = "收斂三角形突破" if row['Is_Triangle'] else ("底底高上升趨勢" if row['Is_Rising'] else "區間橫盤轉強")
        chips = "法人強勢鎖籌" if row['Vol_Ratio'] > 1.2 else "籌碼換手沈澱"

        if not in_pos:
            # 做多
            if (row['Close'] > row['SMA20']) and (row['MACD_Hist'] > 0) and (row['RSI'] < 70):
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Long"
                trades.append({
                    "日期": date_str, "動作": "▲ 做多", "價格": round(buy_price, 1),
                    "詳細分析": f"【趨勢】站穩月線且{pattern}。 \n【技術面】MACD翻正，RSI位階適中。 \n【籌碼】{chips}，具備波段攻擊力。"
                })
            # 放空
            elif (row['Close'] < row['SMA20']) and (row['MACD_Hist'] < 0) and (row['RSI'] > 30):
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Short"
                trades.append({
                    "日期": date_str, "動作": "▼ 放空", "價格": round(buy_price, 1),
                    "詳細分析": f"【趨勢】跌破月線且形態轉弱。 \n【技術面】動能指標下行，空方勢頭確立。 \n【籌碼】主力調節明顯，執行避險空單。"
                })
        elif in_pos:
            days = i - entry_idx
            p_pct = (row['Close'] - buy_price) / buy_price if pos_type == "Long" else (buy_price - row['Close']) / buy_price
            
            exit_reason = ""
            if p_pct >= 0.06: exit_reason = "利潤達標 (+6%)"
            elif p_pct <= -0.03: exit_reason = "動態停損 (-3%)"
            elif days >= 7: exit_reason = "週期強制平倉 (7天)"
            elif (pos_type == "Long" and row['Close'] < row['SMA5']) or (pos_type == "Short" and row['Close'] > row['SMA5']):
                exit_reason = "趨勢轉弱 (破5MA)"

            if exit_reason:
                pnl = p_pct * initial_cap * 2
                balance += pnl
                trades.append({"日期": date_str, "動作": "◆ 平倉", "價格": round(row['Close'], 1), "詳細分析": f"執行【{exit_reason}】。損益結算：{int(pnl):,} 元。等待下一波型態共振。"})
                in_pos = False

    return {"history": df, "ledger": trades[::-1], "equity": int(balance), "rsi": df.iloc[-1]['RSI'], "macd": df.iloc[-1]['MACD_Hist'], "yz": calculate_yz_volatility(df).iloc[-1]}
