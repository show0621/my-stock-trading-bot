import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai
import json

def get_ai_expert_report(ticker_symbol, ticker_name, api_key):
    """LLM 投研代理人：聯網抓取最新新聞並進行深度分析"""
    if not api_key:
        return {"利多":"未輸入 API Key","利空":"無法啟動 AI 分析","展望":"請於側邊欄設定","利基":"---","題材":"---","機率":{"多":33,"空":33,"盤":34}}
    
    try:
        # 1. 抓取即時情資
        tkr = yf.Ticker(ticker_symbol)
        news = tkr.news[:8] # 抓取最新 8 則新聞
        info = tkr.info
        
        context = f"公司：{ticker_name} ({ticker_symbol})\n"
        context += f"產業：{info.get('sector')} - {info.get('industry')}\n"
        context += "最新新聞摘要：\n"
        for n in news:
            context += f"- {n.get('title')}\n"
            
        # 2. 配置 Gemini API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        你現在是頂尖外資券商首席分析師。請針對以下資料進行「極度深度」的投資研究。
        資料內容：{context}
        
        請嚴格依照以下 JSON 格式輸出(不要有 markdown 標籤，只要純 JSON 字串)：
        {{
            "利多": "分析最新利多題材，並在括號標註網路觸及率百分比",
            "利空": "分析目前面臨的風險與負面動態，並標註觸及率百分比",
            "展望": "給出具備前瞻性的 2026 展望分析",
            "利基": "說明該公司核心競爭力或產業地位",
            "題材": "總結目前市場最關注的法說會或產業焦點",
            "機率": {{"多": 數字, "空": 數字, "盤": 數字}}
        }}
        輸出規則：語氣必須專業、犀利。內容要包含具體的細節（如低軌衛星、CoWoS 等），機率總和需為 100。
        """
        
        response = model.generate_content(prompt)
        # 移除可能存在的 Markdown 代碼塊標記
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        return {"利多":"AI 分析暫時離線","利空":str(e),"展望":"請稍後再試","利基":"---","題材":"---","機率":{"多":0,"空":0,"盤":100}}

def calculate_yz_volatility(df, window=20):
    try:
        log_ho, log_lo = np.log(df['High']/df['Open']), np.log(df['Low']/df['Open'])
        log_co, log_oc = np.log(df['Close']/df['Open']), np.log(df['Open']/df['Close'].shift(1))
        v_o = log_oc.rolling(window).var()
        v_c = log_co.rolling(window).var()
        v_rs = (log_ho*(log_ho-log_co)+log_lo*(log_lo-log_co)).rolling(window).mean()
        k = 0.34/(1.34+(window+1)/(window-1))
        return np.sqrt((v_o+k*v_c+(1-k)*v_rs)*252)
    except: return pd.Series(0.3, index=df.index)

def get_trading_signal(ticker, name, cap, api_key):
    try:
        df = yf.download(ticker, period="2y", progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = [c[0] for c in df.columns]
        df = df.dropna()
        df['S20'], df['S60'], df['S120'] = (np.where(df['Close']>df['Close'].shift(x), 1, -1) for x in [20, 60, 120])
        df['Confidence'] = ((df['S20']+df['S60']+df['S120'])/3).clip(lower=0)
        df['YZ_Vol'] = calculate_yz_volatility(df)
        df['Weight'] = (0.3/df['YZ_Vol']*df['Confidence']).clip(upper=1.0)
        df['Sup'], df['Res'] = df['Low'].rolling(20).min(), df['High'].rolling(20).max()
        df['SL'], df['TP'] = df['Close']*0.97, df['Close']*1.06
        cash, shares, buy_p, equity, trades = cap, 0, 0, cap, []
        for i in range(120, len(df)):
            row, date = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
            prev_w, curr_w = df['Weight'].iloc[i-1], row['Weight']
            if curr_w > 0 and prev_w == 0:
                buy_p = row['Close']
                shares = (equity * curr_w) / buy_p
                cash = equity - (equity * curr_w)
                trades.append({"日期":date,"動作":"▲ 買進建倉","價格":round(buy_p,1),"餘額":int(equity),"分析":f"**【TSMOM 動能進場】** 信心:{row['Confidence']:.2f}。波動率:{row['YZ_Vol']:.1%}。投入資金:{int(equity*curr_w):,} TWD。"})
            elif curr_w == 0 and prev_w > 0:
                profit = shares * (row['Close'] - buy_p)
                cash += (shares * row['Close'])
                equity = cash
                shares = 0
                trades.append({"日期":date,"動作":"◆ 平倉保護","價格":round(row['Close'],1),"餘額":int(equity),"分析":f"**【動能衰減平倉】** 分數降至:{row['Confidence']:.2f}。結算損益:**{profit:+.0f} TWD**。"})
            if shares > 0: equity = cash + (shares * row['Close'])
        return {"history":df, "ledger":trades[::-1], "equity":int(equity), "report":get_ai_expert_report(ticker, name, api_key), "stats":df.iloc[-1]}
    except: return None
