import yfinance as yf
import pandas as pd
import numpy as np

def get_expert_report(ticker_name, ticker_symbol):
    """資深分析師 - 深度雙向新聞與題材分析 (含網路觸及率)"""
    # 模擬 2026.04 深度投研數據
    if any(x in ticker_symbol for x in ["2330", "2454", "3711"]):
        return {
            "利多": "2奈米良率超預期、CoWoS產能滿載至2027。 (觸及率: 92%)",
            "利空": "電價上漲衝擊毛利約0.5%、地緣政治出口管制雜音。 (觸及率: 45%)",
            "展望": "AI 營收佔比將於 2026 Q4 突破 45%，進入結構性獲利爆發期。",
            "題材": "4/16法說上修全年展望，2奈米 A16 製程確認首批客戶訂單。",
            "利基": "全球唯一具備先進製程定價權，護城河極深。",
            "機率": {"多": 72, "空": 8, "盤": 20}
        }
    elif any(x in ticker_symbol for x in ["2317", "2382", "6669"]):
        return {
            "利多": "GB200 訂單能見度直達 2027、液冷整機櫃毛利貢獻提前。 (觸及率: 88%)",
            "利空": "供應鏈被動元件短缺導致出貨微幅遞延。 (觸及率: 30%)",
            "展望": "AI 伺服器營收翻倍，電動車業務預計 2027 成為第二成長引擎。",
            "題材": "鴻海 GB200/GB300 全球市佔穩定第一。廣達法說強調液冷技術轉型。",
            "利基": "全球最強垂直整合與供應鏈管理能力。",
            "機率": {"多": 65, "空": 10, "盤": 25}
        }
    else:
        return {
            "利多": "權值股高殖利率護體、避險資金穩定流入。 (觸及率: 40%)",
            "利空": "成交量集中 AI 板塊，傳產標的資金排擠效益。 (觸及率: 55%)",
            "展望": "營運展望正向，聚焦於自動化產線升級與股利發放率提升。",
            "題材": "高股息 ETF (如 0056/00940) 成分股調整帶動被動買盤。",
            "利基": "具備強大現金流與領先之市場佔有率。",
            "機率": {"多": 50, "空": 20, "盤": 30}
        }

def calculate_yz_volatility(df, window=20):
    try:
        log_ho = np.log(df['High'] / df['Open'])
        log_lo = np.log(df['Low'] / df['Open'])
        log_co = np.log(df['Close'] / df['Open'])
        log_oc = np.log(df['Open'] / df['Close'].shift(1))
        v_o = log_oc.rolling(window).var()
        v_c = np.log(df['Close'] / df['Open']).rolling(window).var()
        v_rs = (log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)).rolling(window).mean()
        k = 0.34 / (1.34 + (window + 1) / (window - 1))
        return np.sqrt((v_o + k * v_c + (1 - k) * v_rs) * 252)
    except: return pd.Series(0.30, index=df.index)

def get_trading_signal(ticker, ticker_name, initial_cap=200000):
    df = yf.download(ticker, period="2y", progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # 1. 多尺度訊號 (20/60/120D)
    df['S20'] = np.where(df['Close'] > df['Close'].shift(20), 1, -1)
    df['S60'] = np.where(df['Close'] > df['Close'].shift(60), 1, -1)
    df['S120'] = np.where(df['Close'] > df['Close'].shift(120), 1, -1)
    df['Confidence'] = ((df['S20'] + df['S60'] + df['S120']) / 3).clip(lower=0)
    
    # 2. 波動率與配置
    df['YZ_Vol'] = calculate_yz_volatility(df)
    df['Weight'] = (0.30 / df['YZ_Vol'] * df['Confidence']).clip(upper=1.0)
    
    # 3. 支撐與停損
    df['Sup'], df['Res'] = df['Low'].rolling(20).min(), df['High'].rolling(20).max()
    df['SL'], df['TP'] = df['Close'] * 0.97, df['Close'] * 10.06 # 模擬數值

    # 4. 回測
    balance, trades = initial_cap, []
    for i in range(120, len(df)):
        row, date_str = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
        prev_w = df['Weight'].iloc[i-1]
        if row['Weight'] > 0 and prev_w == 0:
            trades.append({"日期": date_str, "動作": "▲ 進場", "價格": round(row['Close'], 1), "餘額": int(balance), "分析": f"趨勢共振信心: {row['Confidence']:.2f}。波動率 {row['YZ_Vol']:.1%}。"})
        elif row['Weight'] == 0 and prev_w > 0:
            balance += (row['Close'] - df['Close'].iloc[i-5])/df['Close'].iloc[i-5] * initial_cap * prev_w
            trades.append({"日期": date_str, "動作": "◆ 平倉", "價格": round(row['Close'], 1), "餘額": int(balance), "分析": "趨勢轉向或風控觸發，強制空手觀望。"})

    return {
        "history": df, "ledger": trades[::-1], "equity": int(balance), 
        "report": get_expert_report(ticker_name, ticker), "stats": df.iloc[-1]
    }
