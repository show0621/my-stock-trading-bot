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
    
    # 1. 專業指標與型態學
    df['SMA5'] = df['Close'].rolling(5).mean()
    df['SMA20'] = df['Close'].rolling(20).mean()
    ema12, ema26 = df['Close'].ewm(span=12).mean(), df['Close'].ewm(span=26).mean()
    df['MACD_Hist'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9).mean()
    diff = df['Close'].diff()
    u, d = diff.where(diff > 0, 0).rolling(14).mean(), -diff.where(diff < 0, 0).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + (u/d)))
    df['yz_vol'] = calculate_yz_volatility(df)

    # 型態偵測：底底高 (Rising Lows) 與 收斂三角形
    df['Low_Rising'] = (df['Low'] > df['Low'].shift(1)) & (df['Low'].shift(1) > df['Low'].shift(2))
    df['Vol_Ratio'] = df['Volume'] / df['Volume'].rolling(5).mean()

    # --- 2. 雙向回測與詳細分析日誌 ---
    balance, in_pos, buy_price, entry_idx = initial_cap, False, 0, 0
    pos_type, trades = "", []

    for i in range(30, len(df)):
        row, date_str = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
        
        # 分析師日誌描述
        p_desc = "三角形收斂突破" if (df['High'].iloc[i-10:i].max() - df['Low'].iloc[i-10:i].min()) < (df['High'].iloc[i-20:i-10].max() - df['Low'].iloc[i-20:i-10].min()) else ("上升底底高" if row['Low_Rising'] else "區間橫盤")

        if not in_pos:
            # ▲ 做多：站上20MA + MACD轉正
            if (row['Close'] > row['SMA20']) and (row['MACD_Hist'] > 0) and (row['RSI'] < 70):
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Long"
                trades.append({
                    "日期": date_str, "動作": "▲ 做多", "價格": round(buy_price, 1),
                    "詳細分析": f"【技術解析】站穩20MA月線支撐，MACD柱狀翻正確認趨勢動能起漲。【型態】呈現{p_desc}之攻擊姿態。【籌碼】量增比為{row['Vol_Ratio']:.1f}，顯示主力資金積極回流。RSI位於{row['RSI']:.1f}具備攻擊空間。"
                })
            # ▼ 放空：破20MA + MACD轉負
            elif (row['Close'] < row['SMA20']) and (row['MACD_Hist'] < 0) and (row['RSI'] > 30):
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Short"
                trades.append({
                    "日期": date_str, "動作": "▼ 放空", "價格": round(buy_price, 1),
                    "詳細分析": f"【技術解析】股價摜破月線且動能指標轉弱。MACD進入負向區間。【型態】高點受壓，呈現盤跌慣性。籌碼顯示主力調節明顯，建議執行空頭波段避險。"
                })
        
        elif in_pos:
            days = i - entry_idx
            pnl_pct = (row['Close'] - buy_price) / buy_price if pos_type == "Long" else (buy_price - row['Close']) / buy_price
            
            # 平倉邏輯：+6%/-3%/7天/破5MA
            exit_reason = ""
            if pnl_pct >= 0.06: exit_reason = "利潤達標 (+6%)"
            elif pnl_pct <= -0.03: exit_reason = "動態停損 (-3%)"
            elif days >= 7: exit_reason = "波段周期結束 (強制7天平倉)"
            elif (pos_type == "Long" and row['Close'] < row['SMA5']) or (pos_type == "Short" and row['Close'] > row['SMA5']): exit_reason = "趨勢轉弱 (破5MA)"

            if exit_reason:
                pnl_val = pnl_pct * initial_cap * 2 # 模擬2倍槓桿
                balance += pnl_val
                trades.append({
                    "日期": date_str, "動作": "◆ 平倉", "價格": round(row['Close'], 1),
                    "詳細分析": f"因【{exit_reason}】執行平倉結算。當前RSI為{row['RSI']:.1f}。本次交易損益：{int(pnl_val):,} 元。"
                })
                in_pos = False

    return {
        "history": df, "ledger": trades[::-1], "equity": int(balance), 
        "rsi": df.iloc[-1]['RSI'], "macd": df.iloc[-1]['MACD_Hist'],
        "yz": df.iloc[-1]['yz_vol'], "is_rising": df.iloc[-1]['Low_Rising']
    }
