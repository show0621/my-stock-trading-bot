import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

# 1. 初始化配置 (必須是第一行)
st.set_page_config(page_title="2026 量化指揮中心", layout="wide", initial_sidebar_state="collapsed")

# 修正：CSS 大括號必須雙寫 {{}} 才能在 f-string 中正確顯示
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { overscroll-behavior-y: none; }
    .stExpander { background-color: #F7F3E9 !important; border: 1px solid #D6D2C4 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 操盤設定")
    cap = st.number_input("初始資金", value=200000)
    ticker = st.selectbox("監控標的", ["2330.TW", "2317.TW", "2454.TW"])
    t_vol = st.slider("風險目標", 0.05, 0.25, 0.15)

sig = get_trading_signal(ticker, t_vol, cap)
if sig is None:
    st.error("❌ 數據載入失敗，請檢查網路。")
else:
    df = sig['history']
    ledger_df = pd.DataFrame(sig['ledger'])
    price = df.iloc[-1]['Close']
    margin_lot = price * 100 * 0.135

    # --- 2. 專業日式看板 ---
    html_header = f"""
    <div style="background:#F7F3E9; color:#434343; font-family:serif; padding:20px; border-radius:12px; border:2px solid #D6D2C4;">
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:10px; margin-bottom:20px;">
            <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
                <div style="color:#8C8C8C; font-size:10px;">今日現價</div><div style="font-size:22px; font-weight:600;">{price:,}</div>
            </div>
            <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
                <div style="color:#8C8C8C; font-size:10px;">模擬淨值</div><div style="font-size:22px; color:#B18D4D;">{sig['equity']:,}</div>
            </div>
            <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
                <div style="color:#8C8C8C; font-size:10px;">每口保證金</div><div style="font-size:22px;">{int(margin_lot):,}</div>
            </div>
            <div style="background:#FFF; padding:10px; border:1px solid #E5E1D5; text-align:center;">
                <div style="color:#8C8C8C; font-size:10px;">目前訊號</div><div style="font-size:22px; color:{'#9F353A' if sig['macd']>0 else '#434343'};">{'建議持多' if sig['macd']>0 else '建議觀望'}</div>
            </div>
        </div>
        <div style="background:#FFF; padding:15px; border:1px solid #E5E1D5; border-radius:8px; font-size:13px; line-height:1.6;">
            <b style="color:#B18D4D;">⚖️ 7天動態波段策略：RSI + MACD + 形態學</b><br>
            系統嚴格執行 <b>7日強制平倉</b>，並設定 <b>-3% 追蹤止損</b> 與 <b>+6% 目標止盈</b>。目前 RSI 為 {sig['rsi']:.1f}。
        </div>
    </div>
    """
    components.html(html_header, height=320)

    # --- 3. 買賣分析日誌庫 ---
    st.markdown("### 📑 歷史買賣 AI 分析日誌")
    if not ledger_df.empty:
        for _, row in ledger_df.head(10).iterrows():
            with st.expander(f"📅 {row['日期']} - {row['動作']} 價格: {row['價格']}"):
                st.info(row['日誌'])

    # --- 4. 三角形訊號點位視覺化 ---
    st.markdown("### 📈 買賣訊號點位追蹤")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="價格", line=dict(color="#434343", width=1)))

    if not ledger_df.empty:
        # 標註紅三角
        buys = ledger_df[ledger_df['動作'] == "▲ 買進"]
        fig.add_trace(go.Scatter(x=pd.to_datetime(buys['日期']), y=buys['價格'], mode='markers', name='買入', marker=dict(symbol='triangle-up', size=12, color='#9F353A')))
        # 標註綠三角
        sells = ledger_df[ledger_df['動作'] == "▼ 賣出"]
        fig.add_trace(go.Scatter(x=pd.to_datetime(sells['日期']), y=sells['價格'], mode='markers', name='賣出', marker=dict(symbol='triangle-down', size=12, color='#3A5F41')))

    fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=450, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # --- 5. 完整帳本表格 ---
    st.markdown("### 📋 完整操作紀錄表")
    st.dataframe(ledger_df, use_container_width=True)
