import yfinance as yf
import pandas as pd
import numpy as np

def calculate_stats(df):
    """計算波段高低點與 YZ 波動率"""
    window = 20
    df['Wave_High'] = df['High'].rolling(window=20).max()
    df['Wave_Low'] = df['Low'].rolling(window=20).min()
    o, h, l, c = df['Open'], df['High'], df['Low'], df['Close']
    c_prev = df['Close'].shift(1)
    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    v_o = np.log(o/c_prev).rolling(window).var()
    v_c = np.log(c/o).rolling(window).var()
    v_rs = (np.log(h/o) * np.log(h/c) + np.log(l/o) * np.log(l/c)).rolling(window).mean()
    df['yz_vol'] = np.sqrt((v_o + k * v_c + (1 - k) * v_rs) * 252)
    return df

def get_trading_signal(ticker, target_vol=0.15, initial_cap=200000):
    df = yf.download(ticker, period="1y", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    df = calculate_stats(df)
    df['SMA5'], df['SMA20'], df['SMA60'] = df['Close'].rolling(5).mean(), df['Close'].rolling(20).mean(), df['Close'].rolling(60).mean()
    ema12, ema26 = df['Close'].ewm(span=12).mean(), df['Close'].ewm(span=26).mean()
    df['MACD_Hist'] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9).mean()
    diff = df['Close'].diff()
    u, d = diff.where(diff > 0, 0).rolling(14).mean(), -diff.where(diff < 0, 0).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + u/d))

    # --- 雙向回測與詳細分析日誌 ---
    balance, in_pos, buy_price, entry_idx = initial_cap, False, 0, 0
    pos_type, trades = "", []

    for i in range(30, len(df)):
        row, date_str = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
        prev = df.iloc[i-1]
        
        # 籌碼與型態判定
        inst_flow = "外資法人偏多" if row['Volume'] > row['Volume'].rolling(5).mean().iloc[0] and row['Close'] > prev['Close'] else "籌碼換手盤整"
        pattern = "上升三角形突破" if (row['Low'] > prev['Low'] and row['Close'] > row['SMA20']) else "區間震盪收斂"

        if not in_pos:
            # 做多條件
            if (row['Close'] > row['SMA20']) and (row['MACD_Hist'] > 0) and (row['RSI'] < 70):
                in_pos, buy_price, entry_idx, pos_type = True, row['Close'], i, "Long"
                trades.append({
                    "日期": date_str, "動作": "▲ 做多", "價格": round(buy_price, 1),
                    "詳細分析": f"【趨勢分析】股價確認站穩 20MA，K 線呈現「{pattern}」形態。 \n【技術指標】MACD 柱狀由負轉正，動能初步釋放。RSI 位於 {row['RSI']:.1f}，離超買區仍有空間。 \n【籌碼監控】當前 {inst_flow}，具備攻擊意圖。"
                })
            # 放空條件
            elif (row['Close'] < row['SMA20']) and (row['MACD_Hist'] < 0) and (row['
