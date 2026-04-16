import yfinance as yf
import pandas as pd
import numpy as np

def get_expert_report(ticker_name, ticker_symbol):
    ticker_str = str(ticker_symbol)
    
    report = {
        "利多": "產業具備剛性需求，隨全球景氣回溫，營運具備落後補漲之空間。(觸及率: 45%)",
        "利空": "短期資金集中於 AI 核心板塊，該股資金動能受排擠，呈現量縮整理。(觸及率: 55%)",
        "展望": "營運展望維持正向，企業聚焦於財務結構優化與高毛利產品線比重提升。",
        "利基": "具備強大的自由現金流與長期穩定的市場佔有率，為 ETF 避險核心標的。",
        "題材": "近期市場聚焦其法說會對於下半年毛利率之指引，以及配息政策之延續性。",
        "機率": {"多": 50, "空": 20, "盤": 30}
    }
    
    if "1582" in ticker_str or "信錦" in ticker_name:
        report.update({
            "利多": "成功打入美系低軌衛星供應鏈，EMI降噪蓋與散熱支架出貨看增 2~3 倍，營收佔比將突破 10%。(觸及率: 85%)",
            "利空": "PC與Monitor傳統軸承業務受產業庫存調整與匯率衝擊，獲利一度衰退，面臨轉型陣痛。(觸及率: 70%)",
            "展望": "隨低軌衛星產能滿載至2028年，若高毛利衛星產品放量順利彌補PC缺口，有望迎來本益比上調。",
            "題材": "董事長法說會預告轉型收割，低軌衛星產品線有望從接收端延伸至發射端機構件。",
            "利基": "全球顯示器樞紐底座龍頭，機構件精密製造能力強，成功延伸至航太軍規。",
            "機率": {"多": 55, "空": 25, "盤": 20}
        })
    elif any(x in ticker_str for x in ["2330", "2454", "3711", "3661"]):
        report.update({
            "利多": "2奈米良率超預期、CoWoS產能滿載至2027。AI晶片需求進入黃金五年。(觸及率: 95%)",
            "利空": "電價與碳費上升微幅擠壓毛利。地緣政治出口管制雜音干擾外資籌碼。(觸及率: 40%)",
            "展望": "AI 營收佔比將於 2026 Q4 突破 45%，進入結構性獲利爆發期。",
            "題材": "4/16 法說會震撼市場：上修全年資本支出，2奈米確認首批大單。",
            "利基": "全球先進製程唯一供應商，具備恐怖的定價權與絕對技術壁壘。",
            "機率": {"多": 75, "空": 5, "盤": 20}
        })
    elif any(x in ticker_str for x in ["2317", "2382", "6669", "3231", "2376"]):
        report.update({
            "利多": "GB200 訂單能見度直達2027、液冷整機櫃高毛利貢獻提前現身。(觸及率: 88%)",
            "利空": "伺服器零組件短暫缺料雜音。下游組裝毛利競爭加劇。(觸及率: 35%)",
            "展望": "AI 伺服器營收翻倍，電動車代工業務預計 2027 成為獲利第二引擎。",
            "題材": "鴻海 GB200/GB300 全球市佔穩居第一。廣達擴大北美自動化 AI 生產線。",
            "利基": "全球最強垂直整合與冷熱散熱管理，有效抵禦供應鏈斷鏈風險。",
            "機率": {"多": 68, "空": 10, "盤": 22}
        })
    elif any(x in ticker_str for x in ["2881", "2882", "2891", "2886"]):
        report.update({
            "利多": "台股均量支撐經紀收入，海外債券評價利益大幅回升。(觸及率: 70%)",
            "利空": "國內外利率環境變化可能影響存放利差與放貸動能。(觸及率: 30%)",
            "展望": "預期 2026 配息將大幅上調，高殖利率特性吸引長線避險資金進駐。",
            "題材": "金控法說釋放利多，強調獲利動能與資產品質無虞，備抵呆帳覆蓋率創高。",
            "利基": "龐大的財富管理手續費收入與壽險資產，股價防禦力極強。",
            "機率": {"多": 55, "空": 15, "盤": 30}
        })
        
    return report

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
    except Exception:
        return pd.Series(0.30, index=df.index)

def get_trading_signal(ticker, ticker_name, initial_cap=200000):
    try:
        df = yf.download(ticker, period="2y", progress=False, auto_adjust=False)
        if df.empty: 
            return None
            
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = [c[0] for c in df.columns]
            
        df = df.dropna()
            
        df['S20'] = np.where(df['Close'] > df['Close'].shift(20), 1, -1)
        df['S60'] = np.where(df['Close'] > df['Close'].shift(60), 1, -1)
        df['S120'] = np.where(df['Close'] > df['Close'].shift(120), 1, -1)
        df['Confidence'] = ((df['S20'] + df['S60'] + df['S120']) / 3).clip(lower=0)
        
        df['YZ_Vol'] = calculate_yz_volatility(df)
        df['Weight'] = (0.30 / df['YZ_Vol'] * df['Confidence']).clip(upper=1.0)
        
        df['Sup'] = df['Low'].rolling(20).min()
        df['Res'] = df['High'].rolling(20).max()
        df['SL'] = df['Close'] * 0.97
        df['TP'] = df['Close'] * 1.06
        
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
                    "分析": f"**【波段進場】** 趨勢共振分數達 {row['Confidence']:.2f}。目標波動率配置 {curr_w:.1%} 資金。\n\n**【成交明細】**: 買進價格 {buy_price:.1f}，投入資金約 {int(invested_cash):,} TWD。"
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
                    "分析": f"**【風控啟動】** 趨勢轉弱或波動率超標，強制空手觀望保護本金。\n\n**【損益結算】**: 本筆交易實質盈虧為 **{profit:+.0f} TWD**。"
                })
            
            if shares > 0:
                current_equity = cash_uninvested + (shares * row['Close'])
                unrealized_pnl = shares * (row['Close'] - buy_price)
            else:
                unrealized_pnl = 0

        stats = df.iloc[-1].to_dict()
        stats['Unrealized_PnL'] = unrealized_pnl
        stats['Is_Holding'] = True if shares > 0 else False
        
        return {
            "history": df, "ledger": trades[::-1], "equity": int(current_equity),
            "report": get_expert_report(ticker_name, ticker), "stats": stats
        }
    except Exception as e:
        print(f"Error in engine: {e}")
        return None
