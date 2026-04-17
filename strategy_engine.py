"""
策略名稱：TSMOM 多重時間尺度量化策略
作者：李孟霖
版本：20260416-V01-Groq (Llama-3-70B 光速運算版)
"""
import yfinance as yf
import pandas as pd
import numpy as np
from groq import Groq
import json
import streamlit as st

@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_expert_report(ticker_symbol, ticker_name, api_key):
    """LLM 投研代理人：Groq Llama-3 光速分析引擎"""
    
    try:
        tkr = yf.Ticker(ticker_symbol)
        news_data = tkr.news[:6] 
        info = tkr.info
    except:
        news_data = []
        info = {}

    if not api_key:
        return _fallback_scraper_report("未輸入 Groq API Key", news_data)
    
    try:
        context = f"公司：{ticker_name} ({ticker_symbol})\n"
        context += f"產業：{info.get('sector', '未知')} - {info.get('industry', '未知')}\n"
        context += "最新新聞摘要：\n"
        for n in news_data:
            context += f"- {n.get('title', '')}\n"
            
        # 初始化 Groq 晶片連線
        client = Groq(api_key=api_key)
        
        prompt = f"""
        你現在是頂尖外資券商首席分析師。請針對以下資料進行「極度深度」的投資研究，並使用繁體中文回答。
        資料內容：{context}
        
        請嚴格依照以下 JSON 格式輸出(不要有 markdown 標籤，只要純 JSON 字串)：
        {{
            "利多": "分析最新利多題材",
            "利空": "分析目前面臨的風險與負面動態",
            "展望": "給出具備前瞻性的未來展望分析",
            "利基": "說明該公司核心競爭力或產業地位",
            "題材": "總結目前市場最關注的焦點",
            "機率": {{"多": 數字, "空": 數字, "盤": 數字}}
        }}
        機率總和需為 100。
        """
        
        # 呼叫 Llama-3 70B 模型，並強制鎖定 JSON 輸出格式
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "你是一個專門輸出 JSON 格式的頂尖金融分析師。"},
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192",
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        clean_json = chat_completion.choices[0].message.content.strip()
        return json.loads(clean_json)
        
    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            reason = "API 請求過於頻繁 (Rate Limit)"
        else:
            reason = f"AI 模型連線異常 ({error_msg[:30]})"
        return _fallback_scraper_report(reason, news_data)

def _fallback_scraper_report(reason, news_data):
    if not news_data:
        news_str = "無法抓取到近期新聞。"
    else:
        news_str = "<br>".join([f"🔸 {n.get('title', '無標題')}" for n in news_data])

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
