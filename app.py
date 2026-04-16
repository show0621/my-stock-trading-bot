import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

st.set_page_config(page_title="2026 量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

# 1. 介面頂部設定
with st.sidebar:
    st.title("🎐 操盤設定")
    cap = st.number_input("初始資金", value=200000)
    ticker = st.selectbox("監控標的", ["2330.TW", "2317.TW", "2454.TW"])
    t_vol = st.slider("風險目標", 0.05, 0.25, 0.15)

sig = get_trading_signal(ticker, t_vol, cap)
df = sig['history']
ledger_df = pd.DataFrame(sig['ledger'])
latest_price = df.iloc[-1]['Close']

# --- 2. 核心功能區：日式精確計算看板 (保留原本功能) ---
# 計算今日即時數據
margin_per_lot = latest_price * 100 * 0.135
suggested_lots = 4 # 範例固定
total_cost = (latest_price * 100 * 0.00002 * 2 + 40) * suggested_lots

html_header = f"""
<div style="background:#F7F3E9; color:#434343; font-family:serif; padding:20px; border-radius:12px; border:2px solid #D6D2C4;">
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:10px; margin-bottom:20px;">
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">現價</div><div style="font-size:22px; font-weight:600;">{latest_price:,}</div>
        </div>
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">模擬淨值</div><div style="font-size:22px; color:#B18D4D;">{sig['equity']:,}</div>
        </div>
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">每口保證金</div><div style="font-size:22px;">{int(margin_per_lot):,}</div>
        </div>
        <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
            <div style="color:#8C8C8C; font-size:10px;">建議口數</div><div style="font-size:22px; color:#9F353A;">{suggested_lots} 口</div>
        </div>
    </div>
    <div style="background:#FFF; padding:15px; border:1px solid #E5E1D5; border-radius:8px; font-size:13px; line-height:1.6;">
        <b style="color:#B18D4D;">📖 策略執行日誌 (動態風控系統)</b><br>
        本系統採 <b>7日強制平倉機制</b>，並結合 <b>-3% 追蹤止損</b> 與 <b>+6% 目標止盈</b>。
        當前標的：{ticker} | 預估交易成本：約 {int(total_cost)} 元。
    </div>
</div>
"""
components.html(html_header, height=360)

# --- 3. 每次買賣分析日誌 (展開式列表) ---
st.markdown("### 📑 歷史買賣分析日誌庫")
for idx, row in ledger_df.iterrows():
    with st.expander(f"{row['日期']} - {row['動作']} ({row['價格']})"):
        st.write(f"**分析結果：** {row['日誌']}")

# --- 4. 買賣點視覺化 (三角形圖示修復) ---
st.markdown("### 📈 買賣訊號與淨值曲線")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="股價", line=dict(color="#434343", width=1)))

# 標註買入
buys = ledger_df[ledger_df['動作'] == "▲ 買進"]
fig.add_trace(go.Scatter(x=pd.to_datetime(buys['日期']), y=buys['價格'], mode='markers', name='買入', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
# 標註賣出
sells = ledger_df[ledger_df['動作'] == "▼ 賣出"]
fig.add_trace(go.Scatter(x=pd.to_datetime(sells['日期']), y=sells['價格'], mode='markers', name='賣出', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))

fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=500)
st.plotly_chart(fig, use_container_width=True)

# --- 5. 虛擬帳本表格 ---
st.markdown("### 📋 完整操作帳本")
st.dataframe(ledger_df, use_container_width=True)
