import yfinance as yf, pandas as pd, numpy as np, json, os

def get_db_report(sym):
    try:
        with open("ai_database.json", "r", encoding="utf-8") as f: db = json.load(f)
        if sym in db: return db[sym]["report"], db[sym]["chip_type"], db[sym]["update_time"]
    except: pass
    return {"利多":"請在本地執行 update_db.py 更新資料庫","利空":"-","展望":"-","利基":"-","題材":"-","機率":{"多":33,"空":33,"盤":34}}, "未分析", "無資料"

def calculate_yz_volatility(df, w=20):
    try:
        ho, lo, co, oc = np.log(df['High']/df['Open']), np.log(df['Low']/df['Open']), np.log(df['Close']/df['Open']), np.log(df['Open']/df['Close'].shift(1))
        vo, vc = oc.rolling(w).var(), co.rolling(w).var()
        vrs = (ho*(ho-co)+lo*(lo-co)).rolling(w).mean()
        return np.sqrt((vo+0.34/(1.34+(w+1)/(w-1))*vc+(1-0.34/(1.34+(w+1)/(w-1)))*vrs)*252)
    except: return pd.Series(0.3, index=df.index)

def get_trading_signal(sym, cap):
    try:
        df = yf.download(sym, period="2y", progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [c[0] for c in df.columns]
        df = df.dropna()
        df['S20'], df['S60'], df['S120'] = (np.where(df['Close']>df['Close'].shift(x), 1, -1) for x in [20, 60, 120])
        df['Confidence'] = ((df['S20']+df['S60']+df['S120'])/3).clip(lower=0)
        df['YZ_Vol'] = calculate_yz_volatility(df)
        df['Weight'] = (0.3/df['YZ_Vol']*df['Confidence']).clip(upper=1.0)
        cash, shares, eq, trades, bp = cap, 0, cap, [], 0
        for i in range(120, len(df)):
            r, d = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
            pw, cw = df['Weight'].iloc[i-1], r['Weight']
            if cw>0 and pw==0:
                bp = r['Close']
                shares, cash = (eq*cw)/bp, eq-(eq*cw)
                trades.append({"日期":d,"動作":"▲ 買進建倉","價格":round(bp,1),"餘額":int(eq),"分析":f"**【量化進場】** 信心 {r['Confidence']:.2f}，波動率 {r['YZ_Vol']:.1%}。投入 {int(eq*cw):,} TWD。停損看 {r['Low']:.1f}。"})
            elif cw==0 and pw>0:
                profit = shares*(r['Close']-bp)
                cash += shares*r['Close']
                eq, shares = cash, 0
                trades.append({"日期":d,"動作":"◆ 平倉保護","價格":round(r['Close'],1),"餘額":int(eq),"分析":f"**【平倉保護】** 信心降至 {r['Confidence']:.2f}。損益結算: **{profit:+.0f} TWD**。"})
            if shares>0: eq = cash + shares*r['Close']
        rep, ct, ut = get_db_report(sym)
        return {"history":df, "ledger":trades[::-1], "equity":int(eq), "report":rep, "stats":df.iloc[-1], "chip_type":ct, "update_time":ut}
    except: return None
