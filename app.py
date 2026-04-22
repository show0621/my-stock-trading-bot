import streamlit as st

import pandas as pd

import numpy as np

import plotly.graph_objects as go

from FinMind.data import DataLoader

from datetime import datetime, timedelta



# --- [ 1. 系統配置 ] ---

st.set_page_config(page_title="台股量化戰情室 2026 - 李孟霖", layout="wide")



st.sidebar.markdown("---")

st.sidebar.write("👤 **作者：李孟霖**")

st.sidebar.write("📈 **策略參考：Time series momentum & MAD**")

st.sidebar.caption("Tobias J. Moskowitz / 波動收斂與均線發散")

st.sidebar.markdown("---")



FINMIND_TOKEN = st.secrets.get("FINMIND_TOKEN", "").strip()



# --- [ 2. 數據抓取模組 (加入 0 元數據過濾與 MA200 暖機期) ] ---

@st.cache_data(ttl=36000)

def get_stock_data(stock_id, start_date):

    dl = DataLoader()

    if FINMIND_TOKEN:

        try:

            if hasattr(dl, 'login'): dl.login(token=FINMIND_TOKEN)

            else: dl = DataLoader(token=FINMIND_TOKEN)

        except: pass

    try:

        # 🌟 為了算 MAD 的 MA200，偷偷往前多抓 300 天暖機

        fetch_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=300)).strftime('%Y-%m-%d')

        

        df = dl.taiwan_stock_daily(stock_id=stock_id, start_date=fetch_start)

        if df is None or df.empty: return pd.DataFrame()

        df.columns = [c.lower() for c in df.columns]

        df = df.rename(columns={'max': 'high', 'min': 'low'})

        

        chips = dl.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=fetch_start)

        df = df.set_index('date')

        if not chips.empty:

            chips.columns = [c.lower() for c in chips.columns]

            chips_agg = chips.groupby('date').apply(lambda x: float(x['buy'].sum() - x['sell'].sum()))

            df['inst_net'] = chips_agg

        else:

            df['inst_net'] = 0.0

            

        try:

            margin = dl.taiwan_stock_margin_purchase_short_sale(stock_id=stock_id, start_date=fetch_start)

            if not margin.empty:

                margin.columns = [c.lower() for c in margin.columns]

                if 'marginpurchasetodaybalance' in margin.columns:

                    df['margin_bal'] = margin.groupby('date')['marginpurchasetodaybalance'].last()

            else:

                df['margin_bal'] = np.nan

        except:

            df['margin_bal'] = np.nan

            

        df = df.ffill()

        df = df[df['close'] > 0] 

        return df.dropna(subset=['close'])

    except Exception as e: 

        print(f"Fetch Error: {e}")

        return pd.DataFrame()



@st.cache_data(ttl=3600)

def analyze_local_news(stock_id):

    dl = DataLoader()

    try:

        start_news = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')

        news = dl.taiwan_stock_news(stock_id=stock_id, start_date=start_news)

        if news is None or news.empty:

            return "近期無重大新聞", 0, "🧊 缺乏新聞熱度，無資金群聚跡象。"



        titles = " ".join(news['title'].tolist())

        pos_words = ['成長', '創高', '增加', '看好', '買超', '突破', '盈餘', '雙位數', '擴產', '旺季', '受惠', '大漲', '利多']

        neg_words = ['衰退', '下跌', '減少', '看淡', '賣超', '跌破', '虧損', '探底', '停工', '淡季', '風險', '大跌', '利空']



        hot_keywords = ['AI', '伺服器', '散熱', '半導體', '重電', '光通訊', '矽光子', '機器人', 'CoWoS', '輝達', 'NVIDIA', '低軌衛星', '綠能']

        found_hot = [k for k in hot_keywords if k in titles]

        if found_hot:

            sector_text = f"🔥 **位於市場熱門資金板塊** (偵測題材：{', '.join(set(found_hot))})，具備資金流動炒作動能！"

        else:

            sector_text = "🧊 **未見明顯炒作題材**，該股目前並非市場一線資金匯聚板塊，動能可能較為溫吞。"



        pos_score = sum(titles.count(w) for w in pos_words)

        neg_score = sum(titles.count(w) for w in neg_words)



        if pos_score > neg_score * 1.5: return f"🟢 偏多 (正面詞彙 {pos_score} 次)", 1, sector_text

        elif neg_score > pos_score * 1.5: return f"🔴 偏空 (負面詞彙 {neg_score} 次)", -1, sector_text

        else: return f"⚪ 中性 (多空交雜，正面 {pos_score} 次 / 負面 {neg_score} 次)", 0, sector_text

    except:

        return "新聞模組無法讀取", 0, "🧊 無法判定資金板塊。"



# --- [ 3. 回測引擎 (整合 TSM 與 MAD 動態濾網) ] ---

def run_master_backtest(df, initial_capital, user_start_date, use_tsm, use_mad, f_trend, f_vol, f_gap):

    # 共同與 TSM 指標

    tr = pd.concat([df['high']-df['low'], np.abs(df['high']-df['close'].shift()), np.abs(df['low']-df['close'].shift())], axis=1).max(axis=1)

    df['atr'] = tr.rolling(14).mean()

    df['momentum'] = df['close'].pct_change(20)

    df['vol_ma20'] = df['trading_volume'].rolling(20).mean() if 'trading_volume' in df.columns else 1

    df['max_20'] = df['high'].rolling(20).max()

    df['prev_high'] = df['high'].shift(1)

    

    # MAD 核心指標與 F1~F3 條件

    df['ma21'] = df['close'].rolling(21).mean()

    df['ma200'] = df['close'].rolling(200).mean()

    df['mrat'] = df['ma21'] / df['ma200']

    

    df['mad_f1'] = df['close'] / df['max_20'] > 0.88

    

    df['min_10'] = df['low'].rolling(10).min()

    df['prev_min_10'] = df['low'].shift(10).rolling(10).min()

    df['mad_f2'] = df['min_10'] > df['prev_min_10']

    

    df['amp_5'] = df['high'].rolling(5).max() - df['low'].rolling(5).min()

    df['prev_amp_10'] = df['high'].shift(5).rolling(10).max() - df['low'].shift(5).rolling(10).min()

    df['mad_f3'] = df['amp_5'] < df['prev_amp_10']

    

    # 標記每個月的最後一個交易日 (產生 MAD 訊號用)

    df['month'] = pd.to_datetime(df.index).month

    df['is_eom'] = df['month'] != df['month'].shift(-1)

    

    # 🌟 指標算完後，把暖機資料切掉

    df = df[df.index >= user_start_date]

    if df.empty: return pd.DataFrame(), pd.DataFrame(), df

    

    cash, pos, entry_price = initial_capital, 0, 0 

    trade_logs, equity_curve = [], []

    mad_signal_pending = False 

    

    for i in range(len(df)):

        date = df.index[i]

        price = float(df['close'].iloc[i])

        if price <= 0: continue

            

        m, atr, inst = df['momentum'].iloc[i], df['atr'].iloc[i], df['inst_net'].iloc[i]

        

        # --- [ TSM 邏輯判定 ] ---

        pass_f1 = (price >= df['max_20'].iloc[i]) if f_trend else True

        pass_f2 = (df['trading_volume'].iloc[i] > df['vol_ma20'].iloc[i] * 1.5) if (f_vol and 'trading_volume' in df.columns) else True

        pass_f3 = (df['open'].iloc[i] > df['prev_high'].iloc[i]) if f_gap else True

        tsm_buy = (m > 0 and inst > 0 and pass_f1 and pass_f2 and pass_f3)

        tsm_sell = (price < entry_price - (2 * atr) or m < 0)

        

        # --- [ MAD 邏輯判定 ] ---

        mad_condition_met = (df['mrat'].iloc[i] > 1.05) and df['mad_f1'].iloc[i] and df['mad_f2'].iloc[i] and df['mad_f3'].iloc[i]

        if df['is_eom'].iloc[i]:

            mad_signal_pending = mad_condition_met

            

        mad_sell = (price < df['ma21'].iloc[i]) 

        

        is_buy, buy_reason = False, ""

        if use_tsm and tsm_buy:

            is_buy, buy_reason = True, "TSM 動能突破"

        if use_mad and mad_signal_pending:

            is_buy, buy_reason = True, ("MAD 收斂換倉" if not buy_reason else "TSM+MAD 共振買點")

            mad_signal_pending = False 

            

        is_sell, sell_reason = False, ""

        if pos > 0:

            if use_tsm and not use_mad and tsm_sell:

                is_sell, sell_reason = True, "TSM 衰退平倉"

            elif use_mad and not use_tsm and mad_sell:

                is_sell, sell_reason = True, "MAD 跌破月線"

            elif use_tsm and use_mad and (tsm_sell or mad_sell):

                is_sell, sell_reason = True, "雙策略保護平倉"



        if is_buy and pos == 0:

            risk_amt = cash * 0.02

            pos = int(risk_amt / (max(1, atr) * 1000))

            if pos > 0:

                entry_price = price

                cash -= (pos * price * 1000)

                trade_logs.append({"日期": date, "動作": "買進", "價格": price, "數量": pos, "損益": 0, "原因": buy_reason})



        elif pos > 0 and is_sell:

            pl = (price - entry_price) * pos * 1000

            cash += (pos * price * 1000)

            trade_logs.append({"日期": date, "動作": "平倉", "價格": price, "數量": 0, "損益": int(pl), "原因": sell_reason})

            pos = 0



        market_val = pos * price * 1000 if pos > 0 else 0

        equity_curve.append({"date": date, "equity": int(cash + market_val)})



    if pos > 0:

        last_p = float(df['close'].iloc[-1])

        trade_logs.append({"日期": df.index[-1], "動作": "未平倉", "價格": last_p, "數量": pos, "損益": int((last_p - entry_price) * pos * 1000), "原因": "持有中"})



    return pd.DataFrame(trade_logs), pd.DataFrame(equity_curve), df



# --- [ 4. 本地端技術面與形態診斷 (已修復縮排與 Unbound 錯誤) ] ---

def get_local_technical_diagnostics(df, stock_id, use_tsm, use_mad):

    # 🌟 0. 初始化關鍵變數，防止 UnboundLocalError

    p_long, p_short, p_neu = 0, 0, 0

    raw_long, raw_short = 0, 0

    suggestion = "📉 數據不足，請重新執行分析。"

    

    last = df.iloc[-1]

    m, inst = last['momentum'], last['inst_net']

    

    recent_20 = df.tail(20)

    max_h, min_l = recent_20['high'].max(), recent_20['low'].min()

    price_range = (max_h - min_l) / last['close']

    

    f1_status = "✅ 達標" if last['close'] >= df['max_20'].iloc[-1] else "❌ 未達標"

    f2_status = "✅ 達標" if ('trading_volume' in df.columns and last['trading_volume'] > df['vol_ma20'].iloc[-1] * 1.5) else "❌ 未達標"

    f3_status = "✅ 達標" if last['open'] > df['prev_high'].iloc[-1] else "❌ 未達標"

    

    mad_f1_txt = "✅" if last['mad_f1'] else "❌"

    mad_f2_txt = "✅" if last['mad_f2'] else "❌"

    mad_f3_txt = "✅" if last['mad_f3'] else "❌"

    mrat_txt = f"{last['mrat']:.2f} (>1.05強勢)" if last['mrat'] > 1.05 else f"{last['mrat']:.2f} (偏弱)"

    

    pattern = "趨勢行進中"

    if price_range < 0.06: pattern = "盤整收斂 (Consolidation)"

    elif recent_20['low'].tail(5).min() > recent_20['low'].head(10).min() and abs(recent_20['high'].tail(5).max() - recent_20['high'].head(10).max()) / last['close'] < 0.03:

        pattern = "上升三角形 (Ascending Triangle)"

    elif recent_20['high'].tail(5).max() < recent_20['high'].head(10).max() and abs(recent_20['low'].tail(5).min() - recent_20['low'].head(10).min()) / last['close'] < 0.03:

        pattern = "下降三角形 (Descending Triangle)"

    

    margin_change = df['margin_bal'].diff(5).iloc[-1] if 'margin_bal' in df.columns else 0

    chip_status = "中性 (多空不明)"

    if inst > 0 and margin_change < 0: chip_status = "✨ 籌碼高度集中 (法人買超，散戶融資退場)"

    elif inst < 0 and margin_change > 0: chip_status = "⚠️ 籌碼凌亂分散 (法人倒貨，散戶融資承接)"

    elif inst > 0 and margin_change > 0: chip_status = "🔥 資金過熱 (法人與散戶同步湧入)"

    elif inst < 0: chip_status = "🧊 動能退潮 (法人偏空操作)"



    news_text, news_score, sector_text = analyze_local_news(stock_id)

    current_ma20 = df['ma21'].iloc[-1]

    pivot = (last['high'] + last['low'] + last['close']) / 3

    trend_txt = "多頭排列" if last['close'] > current_ma20 else "空頭排列"



    # 🌟 1. 根據策略計算原始機率

    if use_mad and not use_tsm:

        # MAD 專屬機率邏輯

        raw_long = max(0, (last['mrat']>1.05)*30 + last['mad_f1']*20 + last['mad_f2']*15 + last['mad_f3']*15 + (news_score>0)*20)

        raw_short = max(0, (last['mrat']<1)*40 + (not last['mad_f1'])*30 + (news_score<0)*30)

    else:

        # 傳統 TSM 專屬機率邏輯

        raw_long = max(0, (m > 0)*30 + (inst > 0)*30 + (last['mad_f1'])*20 + (last['mad_f3'])*10 + (news_score > 0)*10)

        raw_short = max(0, (m < 0)*30 + (inst < 0)*30 + (not last['mad_f1'])*20 + (news_score < 0)*20)

    

    # 🌟 2. 標準化處理，修復 Streamlit progress 報錯 [0.0, 1.0]

    p_long = min(100, int(raw_long))

    p_short = min(100 - p_long, int(raw_short))

    p_neu = max(0, 100 - p_long - p_short)



    # 🌟 3. 動態建議生成

    if p_long >= 60 and "🔥" in sector_text:

        suggestion = f"🚀 **強力買進**：看多機率極高且位於資金炒作風口，建議順勢做多！"

    elif p_long > 50:

        suggestion = f"📈 **建議買進**：具備{'MAD收斂' if use_mad else 'TSM'}多頭動能，可適度建倉。"

    elif p_neu >= 40:

        suggestion = "☕ **建議觀望**：盤整機率偏高，目前缺乏明確方向，請等待表態。"

    elif p_short >= 50 or "凌亂" in chip_status:

        suggestion = "⚠️ **嚴格避險**：空方機率高且籌碼正在流向散戶，應準備停損。"

    else:

        suggestion = "📉 **保持空手**：目前動能未明或偏弱，請遵守紀律等待機會。"



    report_text = f"""

    1. **多空機率與操作建議**：看多 {p_long}% | 看空 {p_short}% | 盤整 {p_neu}%。綜合判定：{suggestion}

    2. **資金流動板塊**：{sector_text}

    3. **策略狀態檢測**：

       - **TSM 濾網**：股性創高({f1_status}) | 資金爆量({f2_status}) | 題材跳空({f3_status})

       - **MAD 濾網**：MRAT={mrat_txt} | F1({mad_f1_txt}) | F2({mad_f2_txt}) | F3({mad_f3_txt})

    4. **籌碼詳細分析**：近 5 日法人與融資餘額(散戶)對比，呈現 **{chip_status}**。且 20 日動能為 {m:.2%}。

    """



    return {"price": int(last['close']), "sup": round(2*pivot - last['high'], 1), "res": round(2*pivot - last['low'], 1),

            "p_long": p_long, "p_short": p_short, "p_neu": p_neu, "report": report_text}



def get_performance_report(equity_df, initial_capital, logs):

    if equity_df.empty: return {"current": initial_capital, "ret": 0, "max_ret": 0, "mdd": 0, "sharpe": 0, "win_rate": 0, "trades": 0}

    current_val = equity_df['equity'].iloc[-1]

    ret = (current_val - initial_capital) / initial_capital

    max_ret = (equity_df['equity'].max() - initial_capital) / initial_capital

    equity_df['cum_max'] = equity_df['equity'].cummax()

    mdd = ((equity_df['equity'] - equity_df['cum_max']) / equity_df['cum_max']).min()

    equity_df['daily_ret'] = equity_df['equity'].pct_change()

    sharpe = (equity_df['daily_ret'].mean() / equity_df['daily_ret'].std() * np.sqrt(252)) if equity_df['daily_ret'].std() != 0 else 0

    

    win_rate = 0

    trades_count = 0

    if not logs.empty:

        closed_trades = logs[logs['動作'] == '平倉']

        trades_count = len(closed_trades)

        if trades_count > 0:

            win_rate = len(closed_trades[closed_trades['損益'] > 0]) / trades_count

            

    return {"current": current_val, "ret": ret, "max_ret": max_ret, "mdd": mdd, "sharpe": sharpe, "win_rate": win_rate, "trades": trades_count}



# --- [ 5. UI 主畫面介面 ] ---

st.title("🚀 量化交易戰情室 - 2026")



with st.sidebar:

    stock_id = st.text_input("股票代碼", "2330")

    start_dt = st.date_input("分析起始日", datetime(2025, 1, 1))

    init_cash = st.number_input("初始資金", value=1000000)

    

    st.markdown("### 🧠 核心交易策略切換")

    use_tsm = st.checkbox("✅ 啟用 TSM 動能策略", value=True)

    use_mad = st.checkbox("✅ 啟用 MAD 收斂策略", value=False)

    

    st.markdown("### 🎛️ TSM 進階濾網 (僅對TSM生效)")

    st.caption("勾選以過濾假突破")

    use_trend_filter = st.checkbox("1. 股性濾網 (創20日新高)", value=False)

    use_vol_filter = st.checkbox("2. 資金流濾網 (爆量1.5倍)", value=False)

    use_gap_filter = st.checkbox("3. 題材濾網 (跳空越過昨高)", value=False)

    

    btn = st.button("執行全方位分析")



if btn:

    if not use_tsm and not use_mad:

        st.error("⚠️ 策略錯誤：請至少勾選一種核心交易策略！")

    else:

        with st.spinner("🔄 正在分析大數據..."):

            start_str = start_dt.strftime('%Y-%m-%d')

            data = get_stock_data(stock_id, start_str)

            

            if not data.empty:

                logs, equity, proc_data = run_master_backtest(data, init_cash, start_str, use_tsm, use_mad, use_trend_filter, use_vol_filter, use_gap_filter)

                perf = get_performance_report(equity, init_cash, logs)

                diag = get_local_technical_diagnostics(proc_data, stock_id, use_tsm, use_mad)

                

                strat_name = "TSM 動能" if use_tsm and not use_mad else "MAD 收斂" if use_mad and not use_tsm else "TSM + MAD 雙保險"

                st.subheader(f"📊 策略績效與風險 ({strat_name})")

                m1, m2, m3 = st.columns(3)

                m1.metric("目前總資金", f"${perf['current']:,.0f}", f"{perf['ret']:.2%}")

                m2.metric("最大報酬率", f"{perf['max_ret']:.2%}")

                m3.metric("夏普比率", f"{perf['sharpe']:.2f}")

                

                m4, m5, m6, m7 = st.columns(4)

                m4.metric("初始資金", f"${init_cash:,.0f}")

                m5.metric("最大回撤 (MDD)", f"{perf['mdd']:.2%}", delta_color="inverse")

                m6.metric("策略勝率", f"{perf['win_rate']:.1%}")

                m7.metric("完成交易次數", f"{perf['trades']} 次")

                st.divider()



                st.subheader(f"🔍 {stock_id} 數據面即時診斷 ({strat_name}視角)")

                c1, c2, c3 = st.columns(3)

                c1.metric("目前股價", f"${diag['price']}")

                c2.metric("支撐位", diag['sup'])

                c3.metric("壓力位", diag['res'])

                

                p1, p2, p3 = st.columns(3)

                p1.progress(diag['p_long']/100, text=f"看多機率: {diag['p_long']}%")

                p2.progress(diag['p_short']/100, text=f"看空機率: {diag['p_short']}%")

                p3.progress(diag['p_neu']/100, text=f"盤整機率: {diag['p_neu']}%")

                

                st.markdown(f"**多維力量化總結：**\n{diag['report']}")

                st.divider()



                st.subheader("📈 買賣路徑圖")

                fig = go.Figure()

                fig.add_trace(go.Candlestick(x=proc_data.index, open=proc_data['open'], high=proc_data['high'], low=proc_data['low'], close=proc_data['close'], name='K線'))

                if not logs.empty:

                    b = logs[logs['動作'] == '買進']

                    fig.add_trace(go.Scatter(x=b['日期'], y=b['價格']*0.98, mode='markers', marker=dict(symbol='triangle-up', size=12, color='red'), name='買進'))

                    s = logs[logs['動作'] == '平倉']

                    fig.add_trace(go.Scatter(x=s['日期'], y=s['價格'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='black'), name='平倉'))

                

                fig.update_layout(height=600, showlegend=True, xaxis=dict(rangeslider=dict(visible=True, thickness=0.04, yaxis=dict(rangemode="fixed"))))

                st.plotly_chart(fig, use_container_width=True)



                st.plotly_chart(go.Figure(data=[go.Scatter(x=equity['date'], y=equity['equity'], fill='tozeroy', name='帳戶權益')]), use_container_width=True)



                st.subheader("📋 詳細策略交易紀錄")

                def style_logs(val):

                    try:

                        v = float(val)

                        if v > 0: return 'color: #ff4b4b; font-weight: bold;'

                        if v < 0: return 'color: #008000; font-weight: bold;'

                    except: pass

                    return 'color: black;'

                

                st.dataframe(logs.style.map(style_logs, subset=['損益']).format({"價格": "{:.1f}", "損益": "{:,.0f}"}), use_container_width=True)

                

                csv = logs.to_csv(index=False).encode('utf-8-sig')

                st.download_button("📥 下載買賣損益報表 (CSV)", csv, f"{stock_id}_trade_report.csv", "text/csv")

            else:

                st.error("⚠️ 無法取得數據！")



st.markdown("---")

st.caption("作者：李孟霖 | 策略參考：Time series momentum & MAD | 數據來源：FinMind API")
