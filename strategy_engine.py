import yfinance as yf, pandas as pd, numpy as np, json, streamlit as st
from groq import Groq

def get_chip_sentiment(r, v_ma):
    v_r = r['Volume']/v_ma if v_ma>0 else 1
    p_c = (r['Close']-r['Open'])/r['Open']
    b_r = abs(r['Close']-r['Open'])/(r['High']-r['Low']+0.001)
    if v_r>2.5 and abs(p_c)<0.02: return "高檔換手盤 (Hand-over)", v_r
    if p_c>0.03 and b_r>0.7: return "外資進攻盤 (Foreign-Led)", v_r
    if 0<p_c<0.02 and 1.2<v_r<2.0: return "投信養券盤 (IT-Led)", v_r
    if v_r>1.8 and b_r<0.3: return "散戶浮額盤 (Retail-Led)", v_r
    return "法人觀望盤 (Neutral)", v_r

@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_expert_report(sym, nm, key, conf, vol, chip):
    try:
        news = yf.Ticker(sym).news
    except: news = []
    if not key: return {"利多":"未輸入 API Key","利空":"-","展望":"-","利基":"-","題材":"-","機率":{"多":33,"空":33,"盤":34}}
    try:
        ctx = f"公司:{nm}({sym})\n籌碼:{chip}\n量化:信心{conf:.2f}, 波動{vol:.1%}\n新聞:{str([n.get('title') for n in news[:3]])}"
        prompt = f"你是外資策略師。資料:{ctx}\n要求:1.詳述產業與法人心態。2.針對「{chip}」解讀。3.利多利空結尾加(觸及率:XX%)。嚴格輸出JSON包含:利多,利空,展望,利基,題材,機率(多,空,盤總和100)"
        res = Groq(api_key=key).chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama-3.3-70b-versatile", response_format={"type":"json_object"})
        return json.loads(res.choices[0].message.content)
    except Exception as e: return {"利多":f"AI分析暫離: {str(e)[:30]}","利空":"-","展望":"-","利基":"-","題材":"-","機率":{"多":33,"空":33,"盤":34}}

def calculate_yz_volatility(df, w=20):
    try:
        ho, lo = np.log(df['High']/df['Open']), np.log(df['Low']/df['Open'])
        co, oc = np.log(df['Close']/df['Open']), np.log(df['Open']/df['Close'].shift(1))
        vo, vc = oc.rolling(w).var(), co.rolling(w).var()
        vrs = (ho*(ho-co)+lo*(lo-co)).rolling(w).mean()
        k = 0.34/(1.34+(w+1)/(w-1))
        return np.sqrt((vo+k*vc+(1-k)*vrs)*252)
    except: return pd.Series(0.3, index=df.index)

def get_trading_signal(sym, nm, cap, key):
    try:
        df = yf.download(sym, period="2y", progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [c[0] for c in df.columns]
        df = df.dropna()
        df['V_MA5'] = df['Volume'].rolling(5).mean()
        df['S20'], df['S60'], df['S120'] = (np.where(df['Close']>df['Close'].shift(x), 1, -1) for x in [20, 60, 120])
        df['Confidence'] = ((df['S20']+df['S60']+df['S120'])/3).clip(lower=0)
        df['YZ_Vol'] = calculate_yz_volatility(df)
        df['Weight'] = (0.3/df['YZ_Vol']*df['Confidence']).clip(upper=1.0)
        cash, shares, eq, trades, bp = cap, 0, cap, [], 0
        for i in range(120, len(df)):
            r, d = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
            ct, vr = get_chip_sentiment(r, df['V_MA5'].iloc[i-1])
            pw, cw = df['Weight'].iloc[i-1], r['Weight']
            if cw>0 and pw==0:
                bp = r['Close']
                shares, cash = (eq*cw)/bp, eq-(eq*cw)
                msg = f"**【量化進場】** 信心 {r['Confidence']:.2f}，波動率 {r['YZ_Vol']:.1%}。投入 {int(eq*cw):,} TWD。\n\n**【籌碼情境】** **{ct}**。量能達均量 {vr:.1f} 倍。\n\n**【防守】** 停損看 {r['Low']:.1f}。"
                trades.append({"日期":d,"動作":"▲ 買進建倉","價格":round(bp,1),"餘額":int(eq),"分析":msg})
            elif cw==0 and pw>0:
                profit = shares*(r['Close']-bp)
                cash += shares*r['Close']
                eq, shares = cash, 0
                msg = f"**【平倉保護】** 信心降至 {r['Confidence']:.2f}。\n\n**【籌碼退場】** 轉為 {ct}。\n\n**【損益結算】** **{profit:+.0f} TWD**。"
                trades.append({"日期":d,"動作":"◆ 平倉保護","價格":round(r['Close'],1),"餘額":int(eq),"分析":msg})
            if shares>0: eq = cash + shares*r['Close']
        fc, _ = get_chip_sentiment(df.iloc[-1], df['V_MA5'].iloc[-2])
        rep = get_ai_expert_report(sym, nm, key, df.iloc[-1]['Confidence'], df.iloc[-1]['YZ_Vol'], fc)
        return {"history":df, "ledger":trades[::-1], "equity":int(eq), "report":rep, "stats":df.iloc[-1], "chip_type":fc}
    except Exception as e: return None
