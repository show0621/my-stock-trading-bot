import yfinance as yf
import pandas as pd
import numpy as np
import os

def calculate_yz_volatility(df, window=20):
    """精確計算 Yang-Zhang 波動率 (考慮隔夜跳空)"""
    # 確保資料是 Series 格式
    o = df['Open']
    h = df['High']
    l = df['Low']
    c = df['Close']
    c_prev = df['Close'].shift(1)
    
    log_ho = np.log(h / o)
    log_lo = np.log(l / o)
    log_co = np.log(c / o)
    log_oc = np.log(o / c_prev)
    log_cc = np.log(c / c_prev)
    
    v_o = log_oc.rolling(window=window).var()
    v_c = log_cc.rolling(window=window).var()
    v_rs = (log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)).rolling(window=window).mean()
    
    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    sigma_sq = v_o + k * v_c + (1 - k) * v_rs
    return np.sqrt(sigma_sq * 252)

def get_trading_signal(ticker, target_vol=0.15):
    # 1. 抓取數據
    df = yf.download(ticker, period="1y", progress=False)
    
    # --- 修正 Multi-Index 問題 ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 確保 Adj Close 存在
    if 'Adj Close' not in df.columns:
        df['Adj Close'] = df['Close']
        
    # 2. 計算動能因子 (20, 60D 投票)
    df['mom_score'] = (df['Adj Close'].pct_change(20) > 0).astype(int) + \
                      (df['Adj Close'].pct_change(60) > 0).astype(int)
    
    # 3. 計算 YZ 波動率
    df['yz_vol'] = calculate_yz_volatility(df)
    
    # 4. 取得最新一筆數據
    latest = df.iloc[-1]
    current_vol = latest['yz_vol']
    mom_score = latest['mom_score']
    
    # 建議持倉比 = (目標波動 / 當前波動) * (動能分數 / 2)
    # 避免分母為 0
    safe_vol = max(current_vol, 0.05)
    pos_size = (target_vol / safe_vol) * (mom_score / 2)
    
    return {
        "price": latest['Adj Close'],
        "volatility": current_vol,
        "mom_score": mom_score,
        "suggested_pos": min(pos_size, 1.2), # 槓桿上限 1.2 倍
        "history": df
    }

if __name__ == "__main__":
    # 此段落供 GitHub Actions 每天自動執行存檔
    tickers = ["2330.TW", "2454.TW", "2317.TW", "^TWII"]
    all_results = []
    
    print("🚀 正在執行每日策略掃描...")
    
    for t in tickers:
        try:
            res = get_trading_signal(t)
            all_results.append({
                "Date": pd.Timestamp.now(tz='Asia/Taipei').strftime('%Y-%m-%d'),
                "Ticker": t,
                "Price": round(res['price'], 2),
                "Volatility": round(res['volatility'], 4),
                "Mom_Score": res['mom_score'],
                "Suggested_Pos": round(res['suggested_pos'], 4)
            })
            print(f"✅ {t} 處理完成")
        except Exception as e:
            print(f"❌ {t} 處理失敗: {e}")
    
    # 產出或更新 CSV 檔
    output_file = "daily_status.csv"
    new_df = pd.DataFrame(all_results)
    
    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file)
        # 合併並去重 (以日期與代號為準)
        combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['Date', 'Ticker'], keep='last')
        combined_df.to_csv(output_file, index=False)
    else:
        new_df.to_csv(output_file, index=False)
        
    print(f"💾 數據已存至 {output_file}")
