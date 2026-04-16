import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import os
from strategy_engine import get_trading_signal

# 初始化網頁
st.set_page_config(page_title="2026 量化操盤日誌", layout="wide")

# --- 1. 側邊欄：帳戶設定 ---
with st.sidebar:
    st.header("🎎 帳戶設定")
    initial_cap = st.number_input("初始資金 (TWD)", value=200000)
    tickers = {
        "台積電 (2330)": "2330.TW",
        "鴻海 (2317)": "2317.TW",
        "聯發科 (2454)": "2454.TW",
        "廣達 (2382)": "2382.TW",
        "台指期模擬 (^TWII)": "^TWII"
    }
    selected_name = st.selectbox("監控標的", list(tickers.keys()))
    ticker = tickers[selected_name]
    target_vol = st.slider("目標風險控管", 0.05, 0.25, 0.15)

# --- 2. 核心數據運算 ---
signal = get_trading_signal(ticker, target_vol)
df = signal['history']
price = round(float(signal['price']), 1)
pos_ratio = round(float(signal['suggested_pos'] * 100), 1)
vol = round(float(signal['volatility'] * 100), 2)
mom = int(signal['mom_score'])

# --- 3. 專業期貨計算邏輯 ---
margin_rate = 0.135
margin_per_lot = price * 100 * margin_rate
target_investment = initial_cap * (pos_ratio / 100)
suggested_lots = int(target_investment / margin_per_lot) if margin_per_lot > 0 else 0

# 稅費與損益
tax_one_way = price * 100 * 0.00002
total_tax = tax_one_way * suggested_lots * 2
total_fee = 20 * suggested_lots * 2
total_cost = total_tax + total_fee
tick_profit = 100 * suggested_lots

# --- 4. 讀取與計算模擬權益 (從紀錄檔) ---
csv_path = "daily_status.csv"
if os.path.exists(csv_path):
    history_df = pd.read_csv(csv_path)
    # 僅篩選目前標的
    ticker_history = history_df[history_df['Ticker'] == ticker].copy()
    # 簡單模擬權益：假設以每日建議口數持有，計算淨值變動
    ticker_history['Daily_Return'] = ticker_history['Price'].pct_change()
    ticker_history['Equity'] = initial_cap * (1 + (ticker_history['Daily_Return'] * ticker_history['Suggested_Pos']).cumsum())
    current_equity = ticker_history['Equity'].iloc[-1] if not ticker_history.empty else initial_cap
else:
    history_df = pd.DataFrame()
    current_equity = initial_cap

equity_change = current_equity - initial_cap

# --- 5. 判定動作與配色 ---
if mom >= 1 and pos_ratio > 10:
    action_text, action_color, bg_light = "🟢 建議建立多單 (Long Position)", "#9F353A", "#FCEEEF"
elif mom == 0 and pos_ratio < 10:
    action_text, action_color, bg_light = "🔴 建議觀望或清倉 (Exit/Neutral)", "#434343", "#F2F2F2"
else:
    action_text, action_color, bg_light = "🟡 部位調整 (Rebalance)", "#B18D4D", "#FDF7E6"

# --- 6. 嵌入日式專業 HTML 介面 ---
html_content = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;600&family=IBM+Plex+Mono&display=swap');
    .jp-container {{ background: #F7F3E9; color: #434343; font-family: 'Noto Serif TC', serif; padding: 25px; border-radius: 12px; border: 2px solid #D6D2C4; }}
    .grid {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 15px; margin-bottom: 25px; }}
    .card {{ background: #FFFFFF; padding: 15px; border: 1px solid #E5E1D5; border-radius: 8px; text-align: center; }}
    .label {{ color: #8C8C8C; font-size: 11px; letter-spacing: 1px; margin-bottom: 8px; text-transform: uppercase; }}
    .value {{ font-family: 'IBM Plex Mono', monospace; font-size: 24px; font-weight: 600; }}
    .action-banner {{ background: {bg_light}; border: 1px solid {action_color}; padding: 18px; border-radius: 8px; margin-bottom: 25px; text-align: center; }}
    .analysis-box {{ background: #FFFFFF; padding: 20px; border-radius: 8px; border: 1px solid #E5E1D5; font-size: 14px; line-height: 1.7; }}
    .section-title {{ color: #B18D4D; font-weight: 600; border-bottom: 1px solid #E5E1D5; margin-bottom: 10px; padding-bottom: 5px; }}
    .highlight {{ color: #9F353A; font-weight: 600; }}
</style>

<div class="jp-container">
    <div class="grid">
        <div class="card"><div class="label">當前市價</div><div class="value">{price:,}</div></div>
        <div class="card"><div class="label">模擬權益 (Equity)</div><div class="value" style="color:{'#9F353A' if equity_change>=0 else '#434343'}">{int(current_equity):,}</div></div>
        <div class="card"><div class="label">建議操作口數</div><div class="value" style="color:#B18D4D">{suggested_lots} 口</div></div>
        <div class="card"><div class="label">建議持倉比</div><div class="value" style="color:{action_color};">{pos_ratio}%</div></div>
    </div>

    <div class="action-banner">
        <div style="font-size:22px; font-weight:600; color:{action_color};">{action_text}</div>
    </div>

    <div class="analysis-box">
        <div class="section-title">📊 交易執行明細</div>
        小型{selected_name}期貨 (1口=100股)，原始保證金率 13.5%：<br>
        • 每口保證金：<span class="highlight">{int(margin_per_lot):,} 元</span> | 建議投入口數：<span class="highlight">{suggested_lots} 口</span><br>
        • 佔用保證金：{int(margin_per_lot * suggested_lots):,} 元 | 剩餘可用資金：{int(current_equity - (margin_per_lot * suggested_lots)):,} 元<br>
        
        <div class="section-title" style="margin-top:15px;">💸 預估稅費與跳動損益</div>
        • 預估期交稅 (0.00002)：{int(total_tax)} 元 | 預估手續費：{int(total_fee)} 元<br>
        • <b>合計摩擦成本：約 {int(total_cost)} 元</b><br>
        • <b>跳動損益：</b>每跳動 1 點，{suggested_lots}口合約損益為 <span class="highlight">{int(tick_profit)} 元</span>。
    </div>
</div>
"""
components.html(html_content, height=520)

# --- 7. 歷史記錄表格 (動態顯示) ---
st.markdown("### 📜 每日觀測與交易紀錄表")
if not history_df.empty:
    display_df = history_df[history_df['Ticker'] == ticker].sort_values(by="Date", ascending=False)
    st.dataframe(
        display_df[['Date', 'Price', 'Volatility', 'Mom_Score', 'Suggested_Pos']],
        column_config={
            "Date": "日期",
            "Price": "當日價格",
            "Volatility": st.column_config.NumberColumn("YZ 波動率", format="%.2f%%"),
            "Mom_Score": "動能評分",
            "Suggested_Pos": st.column_config.ProgressColumn("建議持倉比", min_value=0, max_value=1.2, format="%.2f")
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("尚無歷史紀錄，請等待 GitHub Actions 執行每日存檔。")

# --- 8. 權益曲線圖 ---
if os.path.exists(csv_path) and not ticker_history.empty:
    st.markdown("### 📈 模擬權益變動曲線 (Equity Curve)")
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(x=ticker_history['Date'], y=ticker_history['Equity'], name="模擬權益", line=dict(color="#B18D4D", width=3), fill='tozeroy', fillcolor='rgba(177,141,77,0.1)'))
    fig_equity.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", margin=dict(l=10, r=10, t=10, b=10), height=300)
    st.plotly_chart(fig_equity, use_container_width=True)
