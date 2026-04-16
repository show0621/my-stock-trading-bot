import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 頁面初始化
st.set_page_config(page_title="2026 量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

# 鎖定手機滑動
st.markdown("<style>[data-testid='stAppViewContainer'] {overscroll-behavior-y: none;}</style>", unsafe_allow_html=True)

# --- 側邊欄 ---
with st.sidebar:
    st.title("🎐 操盤導覽")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {"台積電 (2330)": "2330.TW", "鴻海 (2317)": "2317.TW", "聯發科 (2454)": "2454.TW"}
    selected_name = st.selectbox("標的監控", list(tickers.keys()))
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 2. 獲取數據與回測結果 ---
sig = get_trading_signal(tickers[selected_name], target_vol, initial_cap)

if sig:
    df = sig['history']
    price = round(float(sig['price']), 1)
    mom = sig['mom_score']
    vol_val = round(float(sig['volatility'] * 100), 1)
    
    # 介面色彩與訊號文字
    action_text = "🟢 建議持多" if mom >= 1 else "🔴 建議空倉"
    action_color = "#9F353A" if mom >= 1 else "#434343"

    # --- 3. 渲染日式報告 (含訊號與回測淨值) ---
    html_content = f"""
    <div style="background:#F7F3E9; color:#434343; font-family:serif; padding:20px; border-radius:12px; border:2px solid #D6D2C4;">
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:10px; margin-bottom:20px;">
            <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
                <div style="color:#8C8C8C; font-size:10px;">現價</div><div style="font-size:22px; font-weight:600;">{price:,}</div>
            </div>
            <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
                <div style="color:#8C8C8C; font-size:10px;">模擬淨值</div><div style="font-size:22px; color:#B18D4D;">{sig['equity']:,}</div>
            </div>
            <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
                <div style="color:#8C8C8C; font-size:10px;">YZ 波動率</div><div style="font-size:22px;">{vol_val}%</div>
            </div>
            <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
                <div style="color:#8C8C8C; font-size:10px;">目前訊號</div><div style="font-size:22px; color:{action_color};">{action_text}</div>
            </div>
        </div>
        <div style="background:#FFF; padding:20px; border:1px solid #E5E1D5; border-radius:8px; line-height:1.7; font-size:14px;">
            <b style="color:#B18D4D;">📊 一年期虛擬損益帳本 (最近成交)</b><br>
            系統已根據 YZ 波動率與動能模型，回測 200,000 資金於過去一年的表現。
            目前帳戶淨值估計為 <span style="color:#9F353A; font-weight:600;">{sig['equity']:,} 元</span>。
        </div>
    </div>
    """
    components.html(html_content, height=350)

    # --- 4. 顯示一年回測帳本表格 ---
    st.markdown("### 📋 一年期歷史操作紀錄 (模擬)")
    st.table(pd.DataFrame(sig['ledger']))

    # --- 5. 視覺化 K 線圖 ---
    st.markdown("### 📈 趨勢點位追蹤")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'], name="價格", line=dict(color="#434343")))
    fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("訊號載入失敗，請檢查網路連線。")
