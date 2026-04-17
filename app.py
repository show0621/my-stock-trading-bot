import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from strategy_engine import get_trading_signal

st.set_page_config(page_title="李孟霖 | AI首席投研終端", layout="wide")

# 防斷行 CSS 積木 (完整版面)
css = (
    "<style>"
    ":root{color-scheme:light !important;}"
    ".stApp,.main{background-color:#F7F3E9 !important;}"
    "html,body,p,span,div,h1,h2,h3,h4,h5,h6,label,li{color:#000000 !important;font-family:'Noto Serif TC',serif;}"
    ".status-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;background:#FFFFFF;padding:15px;border-radius:10px;border:1px solid #D6D2C4;margin-bottom:20px;}"
    ".s-title{font-size:12px;color:#666666;text-align:center;}"
    ".s-val{font-size:16px;font-weight:600;color:#000000;text-align:center;}"
    ".report-header{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid #E5E1D5;padding-bottom:10px;margin-bottom:15px;}"
    ".report-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;font-size:14.5px;line-height:1.7;}"
    "@media (max-width:768px){.status-grid{grid-template-columns:repeat(2,1fr);}.report-grid{grid-template-columns:1fr;}}"
    "</style>"
)
st.markdown(css, unsafe_allow_html=True)

with st.sidebar:
    st.title("🎐 AI 投資指揮中心")
    api_k = st.text_input("🔑 Groq API Key", type="password", placeholder="貼上後按 Enter")
    cap = st.number_input("本金設定", value=2000000)
    ind_map = {
        "半導體核心": {"台積電 (2330)": "2330.TW", "聯發科 (2454)": "2454.TW"},
        "AI與伺服器": {"鴻海 (2317)": "2317.TW", "廣達 (2382)": "2382.TW", "緯穎 (6669)": "6669.TW"},
        "🔍 全台股手動輸入": "MANUAL"
    }
    sel_ind = st.radio("📁 產業類別", list(ind_map.keys()))
    if sel_ind == "🔍 全台股手動輸入":
        raw_code = st.text_input("輸入代號", value="2382")
        t_sym, t_nm = f"{raw_code}.TW", f"自選 ({raw_code})"
    else:
        t_nm = st.selectbox("🎯 選擇標的", list(ind_map[sel_ind].keys()))
        t_sym = ind_map[sel_ind][t_nm]

with st.spinner("🚀 AI 正在深度分析籌碼情境..."): 
    sig = get_trading_signal(t_sym, t_nm, cap, api_k)

if sig:
    df, l_df, an, sr = sig['history'], pd.DataFrame(sig['ledger']), sig['report'], sig['stats']
    
    # 狀態牆數值
    v_r, v_s = str(int(sr['High'])), str(int(sr['Low']))
    v_sl, v_tp = str(round(sr['Close']*0.97, 1)), str(round(sr['Close']*1.06, 1))
    v_c, v_v = str(round(sr['Confidence'], 2)), str(round(sr['YZ_Vol']*100, 1))+"%"
    v_w = str(round(sr['Weight']*100, 1))+"%"
    c_type = sig.get("chip_type", "判定中")

    # 狀態牆積木
    sg = (
        f'<div class="status-grid">'
        f'<div><div class="s-title">壓力/支撐</div><div class="s-val">{v_r}/{v_s}</div></div>'
        f'<div><div class="s-title">停損/停利</div><div class="s-val" style="color:#9F353A;">{v_sl}/{v_tp}</div></div>'
        f'<div><div class="s-title">信心/波動</div><div class="s-val">{v_c}/{v_v}</div></div>'
        f'<div><div class="s-title">配置權重</div><div class="s-val" style="color:#B18D4D;">{v_w}</div></div>'
        f'<div><div class="s-title">籌碼主導權</div><div class="s-val" style="color:#3A5F41;">{c_type}</div></div>'
        f'</div>'
    )
    st.markdown(sg, unsafe_allow_html=True)

    # 防呆：預防 KeyError 崩潰
    p_up = an.get("機率", {}).get("多", 33) if isinstance(an.get("機率"), dict) else 33
    p_flat = an.get("機率", {}).get("盤", 34) if isinstance(an.get("機率"), dict) else 34
    p_down = an.get("機率", {}).get("空", 33) if isinstance(an.get("機率"), dict) else 33

    # 報告積木 (還原雙欄佈局)
    rep_1 = '<div style="background:#FFFFFF;padding:20px;border:2px solid #B18D4D;border-radius:12px;color:#000;margin-bottom:20px;">'
    rep_2 = f'<div class="report-header"><h3 style="margin:0;color:#9F353A;">⚖️ AI 首席深度投研報告：{t_nm}</h3><div style="font-size:11px;color:#888;">核心：Llama-3.3 籌碼融合分析</div></div>'
    rep_3 = f'<div class="report-grid"><div><b style="color:#9F353A;">【利多分析】</b><br>{an.get("利多", "分析中...")}<br><br>'
    rep_4 = f'<b style="color:#3A5F41;">【利空分析】</b><br>{an.get("利空", "分析中...")}<br><br>'
    rep_5 = f'<b>【核心利基】</b><br>{an.get("利基", "分析中...")}</div>'
    rep_6 = f'<div><b>【法說/籌碼題材】</b><br>{an.get("題材", "分析中...")}<br><br>'
    rep_7 = f'<b>【未來展望】</b><br>{an.get("展望", "分析中...")}<br><br>'
    rep_8 = f'<b>【機率分布】</b>多頭 <span style="color:#9F353A;font-weight:bold;">{p_up}%</span> | 盤整 {p_flat}% | 空頭 {p_down}%</div></div></div>'
    
    st.markdown(rep_1 + rep_2 + rep_3 + rep_4 + rep_5 + rep_6 + rep_7 + rep_8, unsafe_allow_html=True)

    st.markdown(f"### 💰 帳戶資金變動：總淨值 {sig['equity']:,} TWD", unsafe_allow_html=True)

    # ✅ 完美回歸：多頁顯示與 CSV 下載
    if not l_df.empty:
        col1, col2 = st.columns([1, 1])
        with col1:
            csv_data = l_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 下載完整紀錄 (CSV)", data=csv_data, file_name=f"{t_nm}_Report.csv", mime="text/csv")
        with col2:
            max_p = max(1, (len(l_df)-1)//10+1)
            p_num = st.number_input(f"📄 選擇頁碼 (共 {max_p} 頁)", min_value=1, max_value=max_p, value=1)
            
        start_i = (p_num-1)*10
        end_i = p_num*10
        for _, r in l_df.iloc[start_i:end_i].iterrows():
            with st.expander(f"📅 {r['日期']} | {r['動作']} | 價格: {r['價格']} | 結算: {r['餘額']:,}"): 
                st.markdown(r['分析'])
                
    # ✅ 完美回歸：買賣紅綠三角訊號圖
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="收盤價", line=dict(color="#000", width=1.5)))
    
    if not l_df.empty:
        longs = l_df[l_df['動作'].str.contains("買進")]
        if not longs.empty:
            fig.add_trace(go.Scatter(x=pd.to_datetime(longs['日期']), y=longs['價格'], mode='markers', name='波段進場', marker=dict(symbol='triangle-up', size=16, color='#9F353A')))
            
        shorts = l_df[l_df['動作'].str.contains("平倉")]
        if not shorts.empty:
            fig.add_trace(go.Scatter(x=pd.to_datetime(shorts['日期']), y=shorts['價格'], mode='markers', name='平倉出場', marker=dict(symbol='triangle-down', size=16, color='#3A5F41')))
            
    fig.update_layout(template="plotly_white", paper_bgcolor="#F7F3E9", plot_bgcolor="#F7F3E9", height=400, margin=dict(l=0,r=0,t=20,b=10))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else: 
    st.error("❌ 系統初始化失敗，請檢查網路或代號。")
