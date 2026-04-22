import streamlit as st
import json, os, pandas as pd, yfinance as yf, plotly.graph_objects as go

st.set_page_config(page_title="AI量化分析實驗", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    if not os.path.exists("ai_database.json"): return None
    with open("ai_database.json", "r", encoding="utf-8") as f: return json.load(f)

db = load_data()

# 側邊欄
st.sidebar.title("🏛️ 投研控制中心")
industry_mode = st.sidebar.radio("篩選模式", ["主要產業分類", "手動輸入過濾"])
if db:
    stocks_dict = db.get("stocks", {})
    selected_stock = st.sidebar.selectbox("🚀 選擇監控標的", options=list(stocks_dict.keys()))
else:
    st.sidebar.error("❌ 找不到 ai_database.json")
    st.stop()

# 主畫面
if selected_stock:
    s = stocks_dict[selected_stock]
    q, r = s.get("quant", {}), s.get("report", {})
    
    st.title(f"📊 {selected_stock} | {s.get('name')} 深度研判報告")
    st.success(f"**綜合訊號：{r.get('signal')}** | 核心評分：{r.get('scoring')} | 更新：{s.get('time')}")

    # 第一排：量化指標
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("即時現價", q.get("price"))
    m2.metric("關鍵壓力", q.get("resistance"))
    m3.metric("關鍵支撐", q.get("support"))
    m4.metric("YZ 波動率", q.get("yz_vol"))
    m5.metric("配置權重", f"{int(q.get('weight', 0)*100)}%")

    # 第二排：專業解析
    c1, c2 = st.columns([2, 1])
    with c1:
        st.info(f"**【資深研究主管點評】**\n\n{r.get('industry_analysis')}")
    with c2:
        st.write("**多/空/盤機率分佈**")
        prob = r.get('probability_dist', {"看多": 33, "盤整": 34, "看空": 33})
        st.bar_chart(pd.DataFrame(list(prob.items()), columns=['D', 'P']).set_index('D'), horizontal=True, height=150)

    # 第三排：五大分頁
    tabs = st.tabs(["🔭 技術/結構", "💰 籌碼/基本", "🔥 題材/法說", "🛡️ 風險/回測"])
    with tabs[0]: st.write(r.get("tech_struct"))
    with tabs[1]: st.write(r.get("chips_base"))
    with tabs[2]: st.write(f"題材：{r.get('thematic_catalyst')}\n\n法說預期：{r.get('conference_outlook')}")
    with tabs[3]: 
        st.write(f"🎯 建議停利：{round(q.get('price',0)*1.1, 2)} | 🛑 建議停損：{q.get('support')}")
        st.warning(f"YZ 波動率提示：{q.get('yz_vol')}。建議槓桿：{round(0.3/q.get('yz_vol', 1), 2)}x")

    # 第四排：5年回測圖表
    st.subheader("📈 5 年歷史回測 K 線圖")
    df_all = yf.download(selected_stock, period="5y", progress=False)
    fig = go.Figure(data=[go.Candlestick(x=df_all.index, open=df_all['Open'], high=df_all['High'], low=df_all['Low'], close=df_all['Close'])])
    if "買" in str(r.get("signal")):
        fig.add_annotation(x=df_all.index[-1], y=df_all['Low'].iloc[-1], text="BUY", showarrow=True, arrowhead=1, bgcolor="red", font=dict(color="white"))
    st.plotly_chart(fig, use_container_width=True)

    # 底部 CSV
    csv = pd.DataFrame([{"Ticker": selected_stock, "Price": q.get("price"), "Signal": r.get("signal")}]).to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 下載深度研判報告 (CSV)", csv, f"{selected_stock}.csv", "text/csv")
