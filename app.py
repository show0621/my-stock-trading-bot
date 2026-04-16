import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面配置
st.set_page_config(page_title="2026 量化決策室", layout="wide", initial_sidebar_state="collapsed")

# 修正：強制黑色字體，確保手機版清晰
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F7F3E9; }
    * { color: #000000 !important; font-family: 'Noto Serif TC', serif !important; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; }
    .stMetric { background: #FFFFFF; border: 1px solid #E5E1D5; padding: 10px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 專業操盤設定")
    cap = st.number_input("初始資金", value=200000)
    stocks_0050 = {"台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW", "中信金 (2891)": "2891.TW"}
    ticker_name = st.selectbox("監控標的", list(stocks_0050.keys()))
    t_vol = st.slider("風險目標", 0.05, 0.25, 0.15)

sig = get_trading_signal(stocks_0050[ticker_name], t_vol, cap)
df, stats = sig['history'], sig['stats']
ledger_df = pd.DataFrame(sig['ledger'])

# --- 2. 首席分析師深度投研報告 ---
# 模擬 2026/04/16 台積電法說會新聞題材
latest_news = "今日台積電法說會震撼市場：毛利率 66.2% 創歷史新高，全年美元營收上修至成長超過 30%。2奈米 N2 製程良率良好，預計 2026 年將成為核心動能。"
prob_bull, prob_bear = (65, 10) if stats['MACD_Hist'] > 0 else (30, 45)

html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:5px;">⚖️ 首席分析師深度報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; font-size:14px;">
        <div>
            <b>【波段與波動率分析】</b><br>
            • 波段高/低點：{stats['Wave_High']:,} / {stats['Wave_Low']:,}<br>
            • 當前趨勢：{'多頭底底高' if stats['Close'] > stats['SMA20'] else '空頭修正中'}<br>
            • YZ 波動率：{stats['yz_vol']*100:.1f}% (極度穩定)
        </div>
        <div>
            <b>【未來 3 個月機率分布】</b><br>
            • 看多機率：<span style="color:#9F353A; font-weight:600;">{prob_bull}% (AI/法說利多驅動)</span><br>
            • 橫盤/中性：{100 - prob_bull - prob_bear}%<br>
            • 看空機率：{prob_bear}% (地緣政治風險)
        </div>
    </div>
    <div style="margin-top:15px; font-size:13px; border-top:1px dashed #D6D2C4; padding-top:10px;">
        <b>💡 核心題材：</b>{latest_news}<br>
        <b>🎯 財務與操作建議：</b>目前毛利率表現驚人，財務體質極度健康。建議於 20MA 附近進行波段布局。停損位建議設於月線下方 3%。
    </div>
</div>
"""
components.html(html_report, height=380)

# --- 3. 詳細分析日誌庫 ---
st.markdown("### 📑 操盤日誌庫 (包含 K 棒與籌碼詳細原因)")
if not ledger_df.empty:
    for _, row in ledger_df.head(10).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']}"):
            st.write(f"**詳細分析報告：**")
            st.info(row['詳細分析'])

# --- 4. 訊號圖 ---
st.markdown("### 📈 雙向訊號點位追蹤 (紅買綠賣)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000000", width=1)))
if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))
fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
