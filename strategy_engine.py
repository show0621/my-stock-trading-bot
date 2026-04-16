import yfinance as yf
import pandas as pd
import numpy as np

def calculate_yz_volatility(df, window=20):
    """Yang-Zhang 波動率演算法"""
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
    except Exception:
        return pd.Series(0.30, index=df.index)

def get_dynamic_report(ticker_symbol, conf_score, vol):
    """動態即時情資引擎：連網抓取新聞與公司基本面，並與量化數據連動"""
    ticker_str = str(ticker_symbol)
    
    # 預設模板 (防止斷網時報錯)
    report = {
        "利多": "量化指標顯示目前具備支撐。",
        "利空": "需注意大盤系統性風險與波動率擴張。",
        "展望": "動態載入中...",
        "利基": "動態載入中...",
        "題材": "目前無最新重大新聞。",
        "機率": {"多": 33, "空": 33, "盤": 34}
    }
    
    try:
        # 1. 連網獲取即時物件
        tkr = yf.Ticker(ticker_str)
        info = tkr.info
        news = tkr.news
        
        # 2. 動態生成利基與展望 (基於公司真實資料)
        sector = info.get('sector', '特定產業')
        industry = info.get('industry', '專業領域')
        summary = info.get('longBusinessSummary', '該公司深耕其核心業務，具備一定之市場份額與營運韌性。')
        
        # 翻譯或簡化常見英文 Sector (YFinance 台股常回傳英文)
        report["利基"] = f"深耕於【{sector} - {industry}】板塊，具備該領域之核心競爭力與產能優勢。"
        report["展望"] = f"公司核心業務涵蓋：{summary[:100]}... (受限篇幅擷取)。未來展望將高度連動該產業之終端需求去化速度。"
        
        # 3. 動態抓取最新新聞標題 (最真實的市場題材)
        if news and len(news) > 0:
            news_list = []
            for i, n in enumerate(news[:3]): # 抓最新 3 條
                title = n.get('title', '')
                publisher = n.get('publisher', '市場新聞')
                if title:
                    news_list.append(f"• {title} ({publisher})")
            report["題材"] = "<br>".join(news_list) if news_list else "近期無重大新聞發布。"
        
        # 4. 量化訊號連動：讓多空機率與「真實盤勢」掛鉤
        # 信心分數 (0~1) 決定多方基本盤，波動率決定盤整區間
        bull_prob = int(30 + (conf_score * 40)) # 信心 1.0 時，多頭機率 70%
        if vol > 0.4: # 波動過大，空方與盤整機率上升
            bull_prob -= 10
            
        bull_prob = max(10, min(85, bull_prob)) # 限制在 10% ~ 85% 之間
        neutral_prob = int(20 + (vol * 50)) # 波動率越高，盤整/洗盤機率越高
        neutral_prob = max(10, min(40, neutral_prob))
        bear_prob = 100 - bull_prob - neutral_prob
        
        report["機率"] = {"多": bull_prob, "空": bear_prob, "盤": neutral_prob}
        
        # 5. 利多利空動態判定 (基於技術面狀態)
        if conf_score > 0.6:
            report["利多"] = f"長中短期趨勢共振向上 (信心分數 {conf_score:.2f})，均線呈現多頭排列，買盤積極。(觸及率: 高)"
            report["利空"] = f"短線若乖離過大需留意獲利了結賣壓。當前波動率 {vol:.1%}。(觸及率: 低)"
        elif conf_score == 0:
            report["利多"] = f"目前已回測至低位階，若波動率收斂有望醞釀反彈。(觸及率: 低)"
            report["利空"] = f"技術面全面轉弱 (信心分數 0.00)，跌破關鍵均線，空方勢頭強勁。(觸及率: 高)"
        else:
            report["利多"] = f"下檔具備均線支撐，正處於多空交戰區。(觸及率: 中)"
            report["利空"] = f"上方仍有套牢賣壓待消化，需量能配合方能突破。(觸及率: 中)"
            
    except Exception as e:
        print(f"Info/News Fetch Error: {e}")
        
    return report

def get_trading_signal(ticker, ticker_name, initial_cap=200000):
    try:
        df = yf.download(ticker, period="2y", progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df = df.dropna()
            
        # 1. 多重時間尺度與信心分數
        df['S20'] = np.where(df['Close'] > df['Close'].shift(20), 1, -1)
        df['S60'] = np.where(df['Close'] > df['Close'].shift(60), 1, -1)
        df['S120'] = np.where(df['Close'] > df['Close'].shift(120), 1, -1)
        df['Confidence'] = ((df['S20'] + df['S60'] + df['S120']) / 3).clip(lower=0)
        
        # 2. 波動率與配置
        df['YZ_Vol'] = calculate_yz_volatility(df)
        df['Weight'] = (0.30 / df['YZ_Vol'] * df['Confidence']).clip(upper=1.0)
        
        # 3. 支撐/壓力與停損停利
        df['Sup'] = df['Low'].rolling(20).min()
        df['Res'] = df['High'].rolling(20).max()
        df['SL'] = df['Close'] * 0.97
        df['TP'] = df['Close'] * 1.06
        
        # 4. 回測帳本 (MTM 會計引擎)
        cash_uninvested = initial_cap
        shares = 0
        buy_price = 0
        current_equity = initial_cap
        unrealized_pnl = 0
        trades = []
        
        for i in range(120, len(df)):
            row = df.iloc[i]
            date_str = df.index[i].strftime('%Y/%m/%d')
            prev_w = df['Weight'].iloc[i-1]
            curr_w = row['Weight']
            
            if curr_w > 0 and prev_w == 0:
                buy_price = row['Close']
                invested_cash = current_equity * curr_w
                shares = invested_cash / buy_price
                cash_uninvested = current_equity - invested_cash
                trades.append({
                    "日期": date_str, "動作": "▲ 買進建倉", "價格": round(buy_price, 1), 
                    "餘額": int(current_equity), 
                    "分析": f"**【波段進場】** 趨勢共振啟動 (分數: {row['Confidence']:.2f})。波動率 {row['YZ_Vol']:.1%}，動態配置 {curr_w:.1%} 資金。\n\n**【成交價】**: {buy_price:.1f} TWD。"
                })
            
            elif curr_w == 0 and prev_w > 0:
                sell_price = row['Close']
                realized_cash = shares * sell_price
                profit = realized_cash - (shares * buy_price)
                cash_uninvested += realized_cash
                current_equity = cash_uninvested
                shares = 0
                trades.append({
                    "日期": date_str, "動作": "◆ 平倉保護", "價格": round(sell_price, 1), 
                    "餘額": int(current_equity), 
                    "分析": f"**【風控啟動】** 趨勢轉弱或波動率超標，強制空手觀望。\n\n**【損益結算】**: 本筆交易獲利 **{profit:+.0f} TWD**。"
                })
            
            if shares > 0:
                current_equity = cash_uninvested + (shares * row['Close'])
                unrealized_pnl = shares * (row['Close'] - buy_price)
            else:
                unrealized_pnl = 0

        stats = df.iloc[-1].to_dict()
        stats['Unrealized_PnL'] = unrealized_pnl
        stats['Is_Holding'] = True if shares > 0 else False
        
        # 5. 取得動態報吿 (傳入最後一天的信心分數與波動率)
        dynamic_report = get_dynamic_report(ticker, stats['Confidence'], stats['YZ_Vol'])
        
        return {
            "history": df, "ledger": trades[::-1], "equity": int(current_equity),
            "report": dynamic_report, "stats": stats
        }
    except Exception as e:
        print(f"Engine Error: {e}")
        return None
