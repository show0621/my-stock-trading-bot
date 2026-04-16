import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 配置 (開啟側邊欄)
st.set_page_config(page_title="2026 量化首席終端", layout="wide", initial_sidebar_state="expanded")

# 2. 精確 CSS 修復 (解決選單無法捲動、圖示亂碼、字體黑色優化)
st.markdown("""
<style>
    /* 全局奶油色背景 */
    .stApp { background-color: #F7F3E9; }
    
    /* 文字黑色優化：不干擾圖示系統 */
    p, span, label, h1, h2, h3, .stMarkdown p { color: #000000 !important; font-family: 'Noto Serif TC', serif; }

    /* 側邊欄與選單捲動修正：移除限制 */
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #D6D2C4; }
    div[data-baseweb="select"] * { color: #000 !important; cursor: pointer; }
    div[data-baseweb="popover"] { z-index: 100000 !important; }

    /* Expander 修正 */
    .stExpander { border: 1px solid #D6D2C4 !important; background-color: #FFFFFF !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 專業操盤設定")
    cap = st.number_input("初始帳戶本金", value=200000)
    
    # 擴展後的 0050 全清單
    stocks = {
        "台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW", "台達電 (2308)": "2308.TW", "日月光 (3711)": "3711.TW",
        "中信金 (2891)": "2891.TW", "富邦金 (2881)": "2881.TW", "國泰金 (2882)": "2882.TW",
        "統一 (1216)": "1216.TW", "兆豐金 (2886)": "2886.TW", "中鋼 (2002)": "2002.TW"
    }
    # 下拉選單：現在能正常上下捲動並選擇
    ticker_name = st.selectbox("監控標的 (0050 全權值)", list(stocks.keys()))

# --- 數據獲取 ---
sig = get_trading_signal(stocks[ticker_name], ticker_name, cap)
df, ledger_df = sig['history'], pd.DataFrame(sig['ledger'])
an = sig['report']

# --- 3. 首席分析師投研深度報告 ---
html_report = f"""
<div style="background:#FFFFFF; padding:20px; border:2px solid #B18D4D; border-radius:12px; color:#000;">
    <h3 style="margin-top:0; color:#9F353A; border-bottom:1px solid #E5E1D5;">⚖️ 首席投研報告：{ticker_name}</h3>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; font-size:14.4px; line-height:1.7;">
        <div>
            <b>【產業題材】</b><br>{an['題材']}<br><br>
            <b>【法說會/財務展望】</b><br>{an['法說']}<br>{an['趨勢']}
        </div>
        <div>
            <b>【未來 3 個月機率分布】</b><br>
            • 看多機率：<span style="color:#9F353A; font-weight:600;">{an['看多']}% (核心題材推動)</span><br>
            • 橫盤中性：{100-an['看多']-10}%<br>
            • 看空機率：10%<br><br>
            <b>【統計分布】</b> {an['分布']}
        </div>
    </div>
    <div style="margin-top:15px; font-size:13px; border-top:1px dashed #D6D2C4; padding-top:10px;">
        <b>🎯 專業操作建議：</b>目前 YZ 波動率為 {sig['yz']*100:.1f}%。
        建議於 20MA 支撐位附近佈局，執行 7 天波段與 3% 動態止損策略。
    </div>
</div>
"""
components.html(html_report, height=420)

# --- 4. 財務與損益累積 ---
st.markdown(f"### 💰 帳戶資金變動：目前累積淨值 {sig['equity']:,} TWD (獲利 {sig['equity']-cap:+,})")
# 買賣歷史分析 (恢復 Expander 模式)
st.markdown("### 📑 資深分析師操盤詳細日誌庫")
if not ledger_df.empty:
    for _, row in ledger_df.head(15).iterrows():
        with st.expander(f"📅 {row['日期']} | {row['動作']} | 價格: {row['價格']} | 帳戶餘額: {row['餘額']:,}"):
            st.info(row['分析'])

# --- 5. 訊號圖 (恢復三角形與追蹤) ---
st.markdown("### 📈 雙向訊號點位追蹤 (紅買綠賣)")
fig = go.Figure()
# 價格線
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#000", width=1)))

# 強制繪製訊號點
if not ledger_df.empty:
    longs = ledger_df[ledger_df['動作'] == "▲ 做多"]
    fig.add_trace(go.Scatter(
        x=pd.to_datetime(longs['日期']), y=longs['價格'],
        mode='markers', name='做多',
        marker=dict(symbol='triangle-up', size=14, color='#9F353A')
    ))
    shorts = ledger_df[ledger_df['動作'] == "▼ 放空"]
    fig.add_trace(go.Scatter(
        x=pd.to_datetime(shorts['日期']), y=shorts['價格'],
        mode='markers', name='放空',
        marker=dict(symbol='triangle-down', size=14, color='#3A5F41')
    ))

fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
