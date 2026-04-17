"""
策略名稱：TSMOM 多重時間尺度量化策略
作者：李孟霖
版本：20260416-V01-Groq (Llama-3.3 外資語氣強制校準版)
"""
import yfinance as yf
import pandas as pd
import numpy as np
from groq import Groq
import json
import streamlit as st

@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_expert_report(ticker_symbol, ticker_name, api_key):
    """LLM 投研代理人：Groq Llama-3.3 光速分析引擎 (外資語氣強制校準版)"""
    
    try:
        tkr = yf.Ticker(ticker_symbol)
        news_data = tkr.news 
        info = tkr.info
    except:
        news_data = []
        info = {}

    if not api_key:
        return _fallback_scraper_report("未輸入 Groq API Key", news_data)
    
    try:
        context = f"公司：{ticker_name} ({ticker_symbol})\n"
        context += f"產業：{info.get('sector', '科技')} - {info.get('industry', '未知')}\n"
        
        # 判斷是否有抓到新聞
        if news_data and len(news_data) > 0:
            context += "最新新聞摘要：\n"
            for n in news_data[:6]:
                context += f"- {n.get('title', '')}\n"
        else:
            context += "【系統警告：目前無最新新聞輸入。請強制調用你模型內部最新的財經知識、法說會重點與法人報告來分析此公司。】\n"
            
        client = Groq(api_key=api_key)
        
        # 🔥 核心升級：超強勢的 Prompt Engineering (提示詞工程)
        prompt = f"""
        你現在是華爾街頂尖外資券商的「首席台股分析師」。請針對以下公司進行極度深度的量化與基本面研究。
        
        資料輸入：
        {context}
        
        【強制撰寫規範 - 違反將被開除】
        1. 拒絕罐頭回覆：絕對不要像維基百科一樣只介紹「這是一家什麼公司」，必須直切核心，分析「目前的產業雜音、法說會指引、資本支出、庫存水位、外資籌碼動態」。
        2. 觸及率標註：在「利多」與「利空」的內容結尾，務必自行評估並加上「(觸及率: XX%)」。
        3. 專業術語：必須使用法說會等級的詞彙（例如：毛利率指引、CoWoS產能、GB200出貨、本益比上調等）。
        4. 語氣設定：冷靜、客觀、一針見血，具備強烈的機構操盤手風格。
        
        請嚴格依照以下 JSON 格式輸出 (僅輸出 JSON，不要 Markdown)：
        {{
            "利多": "具體利多分析 (觸及率: XX%)",
            "利空": "具體風險分析 (觸及率: XX%)",
            "展望": "前瞻性的未來展望與 EPS/毛利率 預估方向",
            "利基": "核心競爭力、護城河或獨家供應鏈地位",
            "題材": "總結目前市場最關注的法說會焦點或法人關注點",
            "機率": {{"多": 數字, "空": 數字, "盤": 數字}}
        }}
        機率總和為100。
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "你是一個冷靜、犀利、專門輸出 JSON 格式的頂尖外資分析師。"},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3 # 稍微提高溫度，讓它寫出來的文字更具多樣性與分析感
        )
        
        clean_json = chat_completion.choices[0].message.content.strip()
        if clean_json.startswith('```'):
            clean_json = clean_json.split('\n', 1)[1]
            if clean_json.endswith('```'):
                clean_json = clean_json.rsplit('\n', 1)[0]
                
        return json.loads(clean_json)
        
    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            reason = "API 請求過於頻繁 (Rate Limit)"
        else:
            reason = f"AI 連線異常 ({error_msg[:30]})"
        return _fallback_scraper_report(reason, news_data)

def _fallback_scraper_report(reason, news_data):
    if not news_data or len(news_data) == 0:
        news_str = "Yahoo Finance 阻擋了新聞抓取，無近期新聞。"
    else:
        news_str = "<br>".join([f"🔸 {n.get('title', '無標題')}" for n in news_data[:6]])

    return {
        "利多": f"<span style='color:#888;'>[系統切換為純爬蟲模式，原因：{reason}]</span><br><br><b>【即時新聞聯網抓取】</b><br>{news_str}",
        "利空": "純爬蟲模式無法自動分析風險，請自行判讀上述新聞。",
        "展望": "無 AI 預測支援，請依賴左側量化訊號與 TSMOM 指標操作。",
        "利基": "資料來源：Yahoo Finance API 網路爬蟲",
        "題材": "---",
        "機率": {"多": 33, "空": 33, "盤": 34}
    }

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
