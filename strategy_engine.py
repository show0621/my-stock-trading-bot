"""
策略名稱：TSMOM 籌碼與價量融合策略
版本：20260418-V25-PRO
新增功能：籌碼動態判定、換手情境分析、機構級長文日誌
"""
import yfinance as yf
import pandas as pd
import numpy as np
from groq import Groq
import json
import streamlit as st

def get_chip_sentiment(df_row, avg_vol):
    """
    籌碼與換手情境判定邏輯
    - 外資盤：跳空上漲、長紅Ｋ、收盤接近最高價。
    - 投信盤：成交量溫和放大、連續性小碎步墊高。
    - 散戶盤：巨量長上影線、震盪極大但股價停滯。
    - 換手：成交量突破 2 倍均量，且價格維持在 5MA 之上。
    """
    curr_vol = df_row['Volume']
    vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 1
    price_change = (df_row['Close'] - df_row['Open']) / df_row['Open']
    amplitude = (df_row['High'] - df_row['Low']) / df_row['Open']
    body_ratio = abs(df_row['Close'] - df_row['Open']) / (df_row['High'] - df_row['Low'] + 0.001)

    # 籌碼分類
    if vol_ratio > 2.5 and abs(price_change) < 0.02:
        source = "高檔換手盤 (Hand-over)"
    elif price_change > 0.03 and body_ratio > 0.7:
        source = "外資進攻盤 (Foreign-Led)"
    elif 0 < price_change < 0.02 and 1.2 < vol_ratio < 2.0:
        source = "投信養券盤 (IT-Led)"
    elif vol_ratio > 1.8 and body_ratio < 0.3:
        source = "散戶浮額盤 (Retail-Led)"
    else:
        source = "法人觀望盤 (Neutral)"
        
    return source, vol_ratio

@st.cache_data(ttl=3600, show_spinner=False)
def get_ai_expert_report(ticker_symbol, ticker_name, api_key, confidence, yz_vol, chip_source):
    """Groq Llama-3.3：整合籌碼與價量資訊的深度報告"""
    try:
        tkr = yf.Ticker(ticker_symbol)
        news_data = tkr.news
        info = tkr.info
        
        context = f"公司：{ticker_name} ({ticker_symbol})\n"
        context += f"籌碼現況：{chip_source}\n"
        context += f"量化指標：TSMOM 分數 {confidence:.2f}, YZ 波動率 {yz_vol:.1%}\n"
        context += f"最新新聞摘要：{str([n.get('title') for n in news_data[:3]])}\n"
            
        client = Groq(api_key=api_key)
        prompt = f"""
        你現在是外資首席策略師。請根據以下資料進行深度分析：
        資料：{context}
        
        【強制要求】
        1. 利多/利空必須詳細說明產業結構與法人心態，禁止簡短。
        2. 必須針對「{chip_source}」這個籌碼情境進行換手或資金續航力的解讀。
        3. 利多/利空結尾必須包含「(觸及率: XX%)」。
        
        請嚴格輸出 JSON：
        {{
            "利多": "長篇詳細利多分析",
            "利空": "長篇詳細風險分析",
            "展望": "2026 財測與估值展望",
            "利基": "核心競爭力說明",
            "題材": "目前市場換手或籌碼焦點",
            "機率": {{"多": 數字, "空": 數字, "盤": 數字}}
        }}
        """
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        return {"利多":f"AI分析暫離: {str(e)[:30]}","利空":"---","展望":"---","利基":"---","題材":"---","機率":{"多":33,"空":33,"盤":34}}

def calculate_yz_volatility(df, window=20):
    try:
        log_ho, log_lo = np.log(df['High']/df['Open']), np.log(df['Low']/df['Open'])
        log_co, log_oc = np.log(df['Close']/df['Open']), np.log(df['Open']/df['Close'].shift(1))
        v_o, v_c = log_oc.rolling(window).var(), log_co.rolling(window).var()
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
        df['V_MA5'] = df['Volume'].rolling(5).mean()
        df['S20'], df['S60'], df['S120'] = (np.where(df['Close']>df['Close'].shift(x), 1, -1) for x in [20, 60, 120])
        df['Confidence'] = ((df['S20']+df['S60']+df['S120'])/3).clip(lower=0)
        df['YZ_Vol'] = calculate_yz_volatility(df)
        df['Weight'] = (0.3/df['YZ_Vol']*df['Confidence']).clip(upper=1.0)
        
        cash, shares, buy_p, equity, trades = cap, 0, 0, cap, []
        for i in range(120, len(df)):
            row, date = df.iloc[i], df.index[i].strftime('%Y/%m/%d')
            chip_type, v_ratio = get_chip_sentiment(row, df['V_MA5'].iloc[i-1])
            prev_w, curr_w = df['Weight'].iloc[i-1], row['Weight']
            
            if curr_w > 0 and prev_w == 0:
                buy_p = row['Close']
                shares = (equity * curr_w) / buy_p
                cash = equity - (equity * curr_w)
                # 重新構建詳細日誌
                msg = f"**【TSMOM 量化進場】** 信心分數 {row['Confidence']:.2f}。目前波動率為 {row['YZ_Vol']:.1%}，依風險平價配置 {curr_w:.1%} 資金。\n\n"
                msg += f"**【籌碼情境鑑定】** 當前判斷為：**{chip_type}**。成交量能放大至均量之 {v_ratio:.1f} 倍，顯示主導權由內部資金掌控。\n\n"
                msg += f"**【操盤建議】** 初始防守位看 {row['Low']:.1f}，投入總金額 {int(equity*curr_w):,} TWD。"
                trades.append({"日期":date,"動作":"▲ 買進建倉","價格":round(buy_p,1),"餘額":int(equity),"分析":msg})
            elif curr_w == 0 and prev_w > 0:
                profit = shares * (row['Close'] - buy_p)
                cash +=
