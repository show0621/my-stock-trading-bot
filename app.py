import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 初始化與佈局
st.set_page_config(page_title="2026 量化決策中心", layout="wide", initial_sidebar_state="collapsed")

# 修正：強制黑色字體 CSS (雙大括號預防 f-string 報錯)
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #F7F3E9; overscroll-behavior-y: none; }
    * { color: #000000 !important; }
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; }
    .stAlert { background-color: #FFFFFF !important; border: 1px solid #B18D4D !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 指揮中心設定")
    cap = st.number_input("初始資金", value=200000)
    stocks_0050 = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW", "台達電 (2308)": "2308.TW", "中信金 (2891)": "2891.TW"
    }
    ticker_name = st.selectbox("監控標的 (0050)", list(stocks_0050.keys()))
    t_vol = st.slider("波動率權限", 0.05, 0.25, 0.15)

sig = get_trading_signal(stocks_0050[ticker_name], t_vol, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])

# --- 2. 首席分析師深度投研報告 (2026/04/16 最新台積電法說專欄) ---
# 基於最新搜尋數據模擬
news_report = """台積電今日首季法說創下毛利率 66% 歷史紀錄。資本支出預期上調至 550 億美元，主因 2 奈米產線全面推進。
AI 半導體需求年增 70%，魏哲家強調 AI 將進入結構性高檔。外資法人近期由賣轉買，法人卡位行情明顯。"""
prob_up = 65 if sig['macd'] > 0 else 30

html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5; padding-bottom:5px;">⚖️ 首席分析師深度投研報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; font-size:14px;">
        <div>
            <b>【趨勢與波段解析】</b><br>
            • 當前價格：{df['Close'].iloc[-1]:,}<br>
            • 型態偵測：{'<span style="color:#9F353A;">底底高上升趨勢</span>' if sig['is_rising'] else '區間震盪收斂'}<br>
            • YZ 波動率：{sig['yz']*100:.1f}% (建議 SL -3%)
        </div>
        <div>
            <b>【未來 3 個月機率分布】</b><br>
            • 看多機率：<span style="color:#9F353A; font-weight:600;">{prob_up}% (AI/先進製程驅動)</span><br>
            • 橫盤/中性：{100-prob_up-15}%<br>
            • 看空機率：15% (地緣政治/關稅變數)
        </div>
    </div>
    <div style="margin-top:15px; font-size:13px; border-top:1px dashed #D6D2C4; padding-top:10px;">
        <b>💡 核心題材：</b>{news_report}<br>
        <b>🎯 操作建議：</b>財務表現極度強韌。建議在 RSI 回落至 55 附近時進場。停損設於月線下方 3%，目標波段獲利看 6%-8%。
    </div>
</div>
"""
components.html(html_report, height=380)

# --- 3. 資深操盤日誌庫 ---
st.markdown("### 📑 資深分析師交易日誌 (詳細原因)")
if not ledger_df.empty:
    for _, row in ledger_df.head(10).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']}"):
            st.write(f"**詳細分析報告：**")
            st.info(row['詳細分析'])

# --- 4. 訊號點視覺化 ---
st.markdown("### 📈 雙向訊號點位追蹤 (紅買綠賣)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000000", width=1)))

if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='做多訊號', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='放空訊號', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))

fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=450, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
