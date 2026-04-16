import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面初始化
st.set_page_config(page_title="2026 首席投研終端", layout="wide", initial_sidebar_state="expanded")

# 2. 精確 CSS：解決 _arrow_right 亂碼、字體黑色優化、不遮擋選單
st.markdown("""
<style>
    .stApp { background-color: #F7F3E9; }
    /* 精確指向文字內容，不干擾 Streamlit 原生 SVG Icon */
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stExpander"] span,
    h1, h2, h3, label { color: #000000 !important; font-family: 'Noto Serif TC', serif; }
    
    /* 修正日誌 Icon 亂碼：確保 Icon Font 權重高於黑色 CSS */
    .stExpander svg { fill: #434343 !important; }
    
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 側邊欄
with st.sidebar:
    st.title("🎐 指揮中心設定")
    cap = st.number_input("本金設定", value=200000)
    stocks = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW", "中信金 (2891)": "2891.TW", "長榮 (2603)": "2603.TW"
    }
    ticker_name = st.selectbox("監控標的 (0050)", list(stocks.keys()))

# --- 4. 數據獲取 ---
sig = get_trading_signal(stocks[ticker_name], ticker_name, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
an, st_row = sig['report'], sig['stats']

# --- 5. 操盤狀態牆 (解決數字顯示不全問題) ---
st.markdown(f"""
<div style="background:#FFFFFF; padding:15px; border-radius:10px; border:1px solid #D6D2C4; display:flex; justify-content:space-around; align-items:center; margin-bottom:20px;">
    <div style="text-align:center;"><div style="font-size:12px; color:#666;">高/低點支撐</div><div style="font-size:18px; font-weight:600; color:#000;">{st_row['Res']:.0f} / {st_row['Sup']:.0f}</div></div>
    <div style="text-align:center;"><div style="font-size:12px; color:#666;">建議停損/停利</div><div style="font-size:18px; font-weight:600; color:#9F353A;">{st_row['SL']:.1f} / {st_row['TP']:.1f}</div></div>
    <div style="text-align:center;"><div style="font-size:12px; color:#666;">趨勢信心分數</div><div style="font-size:18px; font-weight:600; color:#000;">{st_row['Confidence']:.2f}</div></div>
    <div style="text-align:center;"><div style="font-size:12px; color:#666;">目前配置權重</div><div style="font-size:18px; font-weight:600; color:#000;">{st_row['Weight']:.1%}/100%</div></div>
</div>
""", unsafe_allow_html=True)

# --- 6. 深度雙向新聞與展望報告 ---
prob = an['機率']
html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:8px;">⚖️ 首席深度投研報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:25px; font-size:14px; line-height:1.7;">
        <div>
            <b style="color:#9F353A;">【利多題材 (觸及率: 高)】</b><br>{an['利多']}<br><br>
            <b style="color:#3A5F41;">【利空風險 (觸及率: 中)】</b><br>{an['利空']}<br><br>
            <b>【核心利基點】</b><br>{an['利基']}
        </div>
        <div>
            <b>【法說動向與題材】</b><br>{an['題材']}<br><br>
            <b>【未來展望 (Outlook)】</b><br>{an['展望']}<br><br>
            <b>【機率分布】</b>多 {prob['多']}% | 空 {prob['空']}% | 盤 {prob['盤']}%
        </div>
    </div>
</div>
"""
components.html(html_report, height=450)

# --- 7. 本金變動帳本 ---
st.markdown(f"### 💰 帳戶資金變動：目前累積淨值 {sig['equity']:,} TWD (盈虧 {sig['equity']-cap:+,})")
if not ledger_df.empty:
    for _, row in ledger_df.head(10).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']} | 本金累積: {row['餘額']:,}"):
            st.info(row['分析'])

# --- 8. 訊號圖 ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1.5)))
if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'].str.contains("進場")]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='進場點', marker=dict(symbol='triangle-up', size=14, color='#9F353A')))
fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500)
st.plotly_chart(fig, use_container_width=True)
