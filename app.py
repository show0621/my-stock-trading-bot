import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面初始化
st.set_page_config(page_title="2026 量化首席終端", layout="wide", initial_sidebar_state="expanded")

# 2. 精確 CSS (黑字、無亂碼、選單滑動)
st.markdown("""
<style>
    .stApp { background-color: #F7F3E9; }
    div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stExpander"] span, h1, h2, h3, label { color: #000000 !important; font-family: 'Noto Serif TC', serif; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    div[data-baseweb="popover"] { z-index: 10000 !important; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# 3. 產業分類別
industry_groups = {
    "半導體/IC核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW", "日月光投控 (3711)": "3711.TW", "世芯 (3661)": "3661.TW"},
    "AI與代工": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW", "緯創 (3231)": "3231.TW"},
    "金融/金控": {"富邦金 (2881)": "2881.TW", "國泰金 (2882)": "2882.TW", "中信金 (2891)": "2891.TW", "兆豐金 (2886)": "2886.TW"},
    "🔍 全台股手動輸入": "MANUAL"
}

with st.sidebar:
    st.title("🎐 專業操盤設定")
    cap = st.number_input("初始帳戶本金", value=200000)
    selected_ind = st.radio("📁 產業類別 (解決選單滑動問題)", list(industry_groups.keys()))
    
    if selected_ind == "🔍 全台股手動輸入":
        code = st.text_input("輸入台股 4 位代號 (如: 2303)", value="2303")
        ticker_symbol, ticker_name = f"{code}.TW", f"自選標的 ({code})"
    else:
        ticker_name = st.selectbox("🎯 選擇公司名稱 (代號)", list(industry_groups[selected_ind].keys()))
        ticker_symbol = industry_groups[selected_ind][ticker_name]

# --- 4. 執行量化引擎 ---
sig = get_trading_signal(ticker_symbol, ticker_name, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
an, st_row = sig['report'], sig['stats']

# --- 5. 首席深度投研報告 ---
prob = an['機率分布']
html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:8px;">⚖️ 首席深度投研報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:25px; font-size:14px; line-height:1.7;">
        <div>
            <b style="color:#9F353A;">【利多題材 (Bullish)】</b><br>{an['利多消息']}<br><br>
            <b style="color:#3A5F41;">【利空風險 (Bearish)】</b><br>{an['利空消息']}<br><br>
            <b>【核心利基點】</b><br>{an['產業利基']}
        </div>
        <div>
            <b>【法說會摘要與動態】</b><br>{an['法說動向']}<br><br>
            <b>【未來展望 (Outlook)】</b><br>{an['未來展望']}<br><br>
            <b>【多空盤整分布機率】</b><br>
            多頭 <span style="color:#9F353A; font-weight:600;">{prob['多']}%</span> | 盤整 {prob['盤']}% | 空頭 {prob['空']}%
        </div>
    </div>
</div>
"""
components.html(html_report, height=480)

# --- 6. 量化監控指標 ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("高/低點支撐", f"{st_row['Resistance']:.0f} / {st_row['Support']:.0f}")
c2.metric("趨勢信心分數", f"{st_row['Confidence']:.2f}")
c3.metric("YZ 年化波動率", f"{st_row['YZ_Vol']:.1%}")
c4.metric("目前配置權重", f"{st_row['Weight']:.1%}")

# --- 7. 損益帳本與詳細日誌 ---
st.markdown(f"### 💰 帳戶資金變動：累積淨值 {sig['equity']:,} TWD (盈虧 {sig['equity']-cap:+,})")
if not ledger_df.empty:
    for _, row in ledger_df.head(15).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']} | 本金變動: {row['餘額']:,}"):
            st.info(row['分析'])

# --- 8. 訊號圖 ---
st.markdown("### 📈 雙向訊號點位追蹤 (紅多綠空)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1.5)))
if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'].str.contains("進場")]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='進場點', marker=dict(symbol='triangle-up', size=14, color='#9F353A')))
st.plotly_chart(fig, use_container_width=True)
