"""
🐵 港股十倍股量化選股系統 - Streamlit Web App
============================================

Author: Ape 仔
適用於香港小型股票

Note: Yahoo Finance 港股代碼格式為 XXXX.HK
例如：騰訊 0700.HK、阿里 9988.HK
"""

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import sys
import os

# 確保路徑正確
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scoring_engine import ScoringEngine, StockScore
from settings import Settings

# 頁面設定
st.set_page_config(
    page_title="港股十倍股篩選器 | HK 10-Bagger",
    page_icon="🐵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #E60012;  /* 港交所紅色 */
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-high {
        color: #00C853;
        font-weight: bold;
    }
    .score-mid {
        color: #FFD600;
        font-weight: bold;
    }
    .score-low {
        color: #FF5252;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #E60012;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
    }
    .hk-badge {
        background-color: #E60012;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def get_hk_stock_data(symbol: str) -> dict:
    """獲取港股數據 (緩存 1 小時)
    
    自動處理代碼格式：
    - 如果輸入 0700 自動轉為 0700.HK
    - 如果輸入 0700.HK 直接使用
    """
    # 標準化代碼
    symbol = symbol.upper().strip()
    if not symbol.endswith('.HK'):
        # 嘗試添加 .HK 後綴
        # 4位數以下的需要補零
        if symbol.isdigit():
            symbol = symbol.zfill(4) + '.HK'
        else:
            symbol = symbol + '.HK'
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 檢查是否有效數據
        if not info.get('regularMarketPrice'):
            return None
        
        data = {
            'symbol': symbol,
            'display_symbol': symbol.replace('.HK', ''),
            'name': info.get('shortName', info.get('longName', symbol)),
            'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
            'market_cap': info.get('marketCap', 0),
            'book_value': info.get('bookValue', 0),
            'price_to_book': info.get('priceToBook', 0),
            'roa': info.get('returnOnAssets', 0) or 0,
            'roe': info.get('returnOnEquity', 0) or 0,
            'ebitda': info.get('ebitda', 0),
            'free_cashflow': info.get('freeCashflow', 0),
            'operating_cashflow': info.get('operatingCashflow', 0),
            'beta': info.get('beta', 1.0),
            '52w_low': info.get('fiftyTwoWeekLow', 0),
            '52w_high': info.get('fiftyTwoWeekHigh', 0),
            'earnings_growth': info.get('earningsGrowth', 0) or 0,
            'revenue_growth': info.get('revenueGrowth', 0) or 0,
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'currency': info.get('currency', 'HKD'),
        }
        
        # 計算衍生指標
        if data['book_value'] > 0 and data['current_price'] > 0:
            data['book_to_market'] = data['book_value'] / data['current_price']
        else:
            data['book_to_market'] = 0
        
        if data['market_cap'] > 0 and data['free_cashflow']:
            data['fcf_yield'] = data['free_cashflow'] / data['market_cap']
        else:
            data['fcf_yield'] = 0
        
        revenue = info.get('totalRevenue', 0)
        if revenue > 0 and data['ebitda'] > 0:
            data['ebitda_margin'] = data['ebitda'] / revenue
        else:
            data['ebitda_margin'] = 0
        
        if data['52w_low'] > 0 and data['current_price'] > 0:
            data['price_to_52w_low'] = data['current_price'] / data['52w_low']
        else:
            data['price_to_52w_low'] = 1.5
        
        data['roa_pct'] = data['roa'] * 100
        data['earnings_growth_pct'] = data['earnings_growth'] * 100
        data['fcf_yield_pct'] = data['fcf_yield'] * 100
        
        # 轉換市值為港幣
        if data['market_cap'] > 0 and data.get('currency') == 'HKD':
            data['market_cap_hkd'] = data['market_cap']
        elif data['market_cap'] > 0:
            # 假設是USD，轉為HKD (7.8固定匯率)
            data['market_cap_hkd'] = data['market_cap'] * 7.8
        else:
            data['market_cap_hkd'] = 0
        
        return data
    except Exception as e:
        return None


def score_stock(data: dict, settings: Settings, engine: ScoringEngine) -> StockScore:
    """為股票評分"""
    stock = StockScore(
        symbol=data['symbol'],
        name=data['name'],
        market_cap=data['market_cap'],  # 使用原始市值（美元）
        book_to_market=data.get('book_to_market', 0),
        roa=data['roa'],
        ebitda=data.get('ebitda_margin', 0),
        fcf_yield=data.get('fcf_yield', 0),
        price_to_52w_low=data.get('price_to_52w_low', 1.5),
        asset_growth=0.05,  # 預設值
        earnings_growth=data['earnings_growth'],
        beta=data['beta'],
        current_price=data['current_price'],
        industry_median_btm=0.5,
        industry_median_fcf=0.05
    )
    
    engine.calculate_total_score(stock)
    stock._raw_data = data
    return stock


def get_score_color(score: float) -> str:
    """根據分數返回顏色"""
    if score >= 70:
        return "🔥"
    elif score >= 55:
        return "👍"
    elif score >= 40:
        return "⚠️"
    else:
        return "❌"


def get_score_class(score: float) -> str:
    if score >= 70:
        return "score-high"
    elif score >= 55:
        return "score-mid"
    else:
        return "score-low"


def format_hkd(amount: float) -> str:
    """格式化港幣金額"""
    if amount >= 1e8:
        return f"HK${amount/1e8:.2f}億"
    elif amount >= 1e6:
        return f"HK${amount/1e6:.2f}百萬"
    else:
        return f"HK${amount:,.0f}"


def main():
    # Header
    st.markdown('<p class="main-header">🐵 港股十倍股量化選股系統</p>', unsafe_allow_html=True)
    st.markdown("""
    <p class="sub-header">
        基於 24 年研究 📈 專為香港小型股票優化 | 市值門檻：5億港幣以下
    </p>
    """, unsafe_allow_html=True)
    
    # 初始化
    settings = Settings()
    engine = ScoringEngine(settings)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<span class="hk-badge">🇭🇰 港股版</span>', unsafe_allow_html=True)
        st.header("📊 系統設定")
        
        st.subheader("🎯 6 個核心準則")
        st.markdown("""
        1. **市值要細** - < HK$5 億
        2. **高價值+高獲利** - B/M、ROA、EBITDA
        3. **強勁現金流** - FCF Yield 高
        4. **低位入場** - 接近 12 個月低位
        5. **資產/盈餘平衡** - 資產增速 < 盈利增速
        6. **利率敏感度** - Beta 值高
        """)
        
        st.divider()
        
        st.subheader("💰 市值範圍 (港幣)")
        st.markdown("""
        - **最大：** HK$5 億
        - **最小：** HK$5,000 萬
        """)
        
        st.divider()
        
        st.subheader("📈 評分標準")
        st.markdown("""
        | 分數 | 等級 |
        |------|------|
        | 70+ | 🔥 強烈建議關注 |
        | 55+ | 👍 具備潛質 |
        | 40+ | ⚠️ 一般 |
        | <40 | ❌ 不符合標準 |
        """)
        
        st.divider()
        
        st.subheader("💡 輸入提示")
        st.markdown("""
        - 輸入 **4位數字** 如 `0700` 會自動轉為 `0700.HK`
        - 直接輸入如 `0700.HK` 也可
        - 騰訊 = 0700、阿里 = 9988
        """)
        
        st.divider()
        
        st.caption("© 2026 港股十倍股篩選系統")
        st.caption("Developed by Ape 仔 🐵")
    
    # Main content
    tab1, tab2 = st.tabs(["🔍 單支股票分析", "📋 批量篩選"])
    
    with tab1:
        st.header("🔍 單支股票分析")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            symbol_input = st.text_input(
                "輸入港股代碼 (4位數字，如 0700, 9988, 1810)",
                value="1810",
                placeholder="輸入代碼...",
                help="輸入4位數字，系統會自動加上 .HK"
            ).upper().strip()
        
        with col2:
            st.write("")
            analyze_btn = st.button("🔎 分析", type="primary", use_container_width=True)
        
        if symbol_input and (analyze_btn or len(symbol_input) >= 1):
            with st.spinner(f"正在分析 {symbol_input}..."):
                data = get_hk_stock_data(symbol_input)
            
            if data:
                stock = score_stock(data, settings, engine)
                
                # 基本資訊
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("💰 現價", f"HK${data['current_price']:.2f}" if data['current_price'] else "N/A")
                col2.metric("🏢 市值", format_hkd(data.get('market_cap_hkd', 0)) if data.get('market_cap_hkd', 0) > 0 else "N/A")
                col3.metric("📉 Beta", f"{data['beta']:.2f}" if data['beta'] else "N/A")
                col4.metric("📅 52W低位", f"{data['price_to_52w_low']:.2f}x" if data['price_to_52w_low'] else "N/A")
                
                # 總評分
                score_class = get_score_class(stock.total_score)
                score_emoji = get_score_color(stock.total_score)
                
                st.markdown(f"""
                <div style="text-align: center; padding: 2rem; background-color: #f8f9fa; border-radius: 1rem; margin: 1rem 0;">
                    <h2 style="margin: 0;">總評分</h2>
                    <h1 style="font-size: 4rem; margin: 0.5rem 0; color: {'#00C853' if stock.total_score >= 70 else '#FFD600' if stock.total_score >= 55 else '#FF5252'};">
                        {stock.total_score:.1f} {score_emoji}
                    </h1>
                    <p style="margin: 0;">{stock.name}</p>
                    <p style="margin: 0; color: #666;">代碼: {data['display_symbol']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 詳細分數
                st.subheader("📊 各項評分詳情")
                
                score_data = {
                    "準則": ["1. 市值分 (<HK$5億)", "2. 價值分", "3. 現金流分", "4. 低位分", "5. 平衡分", "6. 利率敏感度"],
                    "分數": [
                        stock.market_cap_score,
                        stock.value_score,
                        stock.cash_flow_score,
                        stock.price_position_score,
                        stock.balance_score,
                        stock.rate_sensitivity_score
                    ],
                    "權重": ["16.67%", "16.67%", "16.67%", "16.67%", "16.67%", "16.67%"],
                    "加權分": [
                        stock.market_cap_score * 0.1667,
                        stock.value_score * 0.1667,
                        stock.cash_flow_score * 0.1667,
                        stock.price_position_score * 0.1667,
                        stock.balance_score * 0.1667,
                        stock.rate_sensitivity_score * 0.1667
                    ]
                }
                
                df_scores = pd.DataFrame(score_data)
                df_scores['分數'] = df_scores['分數'].round(1)
                df_scores['加權分'] = df_scores['加權分'].round(1)
                
                st.dataframe(df_scores, use_container_width=True, hide_index=True)
                
                # 關鍵指標
                st.subheader("📈 關鍵財務指標")
                
                col1, col2, col3 = st.columns(3)
                
                col1.metric("Book-to-Market", f"{data.get('book_to_market', 0):.3f}")
                col2.metric("ROA", f"{data.get('roa_pct', 0):.2f}%")
                col3.metric("FCF Yield", f"{data.get('fcf_yield_pct', 0):.2f}%")
                
                col1, col2, col3 = st.columns(3)
                
                col1.metric("盈利增長", f"{data.get('earnings_growth_pct', 0):.1f}%")
                col2.metric("52W Low", f"HK${data.get('52w_low', 0):.2f}")
                col3.metric("52W High", f"HK${data.get('52w_high', 0):.2f}")
                
                # 行業
                if data.get('sector'):
                    st.info(f"🏭 行業: {data['sector']} / {data.get('industry', 'N/A')}")
                
                # 評語
                st.divider()
                
                if stock.total_score >= 70:
                    st.success("🔥 **強烈建議關注！** 呢支股票符合多項十倍股特質。")
                elif stock.total_score >= 55:
                    st.info("👍 **具備投資潛質** - 部分指標符合十倍股標準。")
                elif stock.total_score >= 40:
                    st.warning("⚠️ **一般** - 需要更多分析配合判斷。")
                else:
                    st.error("❌ **不太符合** - 建議尋找其他標的。")
                
                st.caption("⚠️ 警告：此系統僅供參考，不構成投資建議。過往表現不代表未來回報。")
                
            else:
                st.error(f"❌ 無法獲取 {symbol_input} 的數據，請檢查代碼是否正確。\n\n💡 提示：輸入4位數字如 0700、1810、9988")
    
    with tab2:
        st.header("📋 批量篩選")
        
        st.markdown("""
        ### 🚀 快捷小型股清單
        以下係熱門小型港股（可自行修改代碼）：
        """)
        
        # 預設股票清單 - 港股小型股
        default_hk_stocks = [
            "1810",  # 小米
            "6618",  # 京東健康
            "6060",  # 眾安在線
            "3759",  # 康希通信
            "2138",  # 醫思健康
            "3309",  # 希瑪眼科
            "1549",  # FSL富線
            "9999",  # 網易
            "0700",  # 騰訊
            "9988",  # 阿里巴巴
            "3690",  # 美團
            "9618",  # 京東
            "1024",  # 快手
            "2638",  # 香港電訊
            "6823",  # 香港寬頻
            "0688",  # 中海外
            "1109",  # 華潤置地
            "0001",  # 長和
            "0016",  # 新鴻基
            "0012",  # 恒生地產
        ]
        
        # 顯示預設清單
        col1, col2 = st.columns([3, 1])
        
        with col1:
            stocks_input = st.text_area(
                "股票代碼 (一行一個，輸入4位數字)",
                value="\n".join(default_hk_stocks),
                height=200,
                help="輸入股票代碼，每行一個"
            )
        
        with col2:
            st.write("")
            st.write("💰 市値篩選:")
            min_market_cap = st.number_input("最小市值 (億HKD)", value=0.0, step=0.5, help="最小市值")
            max_market_cap = st.number_input("最大市值 (億HKD)", value=50.0, step=1.0, help="最大市值")
            
            st.write("")
            top_n = st.slider("顯示 Top N", 5, 50, 20)
        
        stocks_list = [s.strip().upper() for s in stocks_input.strip().split('\n') if s.strip()]
        
        if st.button("🔍 開始批量篩選", type="primary", use_container_width=True):
            if not stocks_list:
                st.warning("請輸入至少一個股票代碼")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                
                for i, symbol in enumerate(stocks_list):
                    display_sym = symbol
                    status_text.text(f"正在分析 {display_sym}... ({i+1}/{len(stocks_list)})")
                    progress_bar.progress((i+1)/len(stocks_list))
                    
                    data = get_hk_stock_data(symbol)
                    
                    if data:
                        # 市値過濾 (轉為港幣計算)
                        market_cap_hkd = data.get('market_cap_hkd', 0)
                        
                        if market_cap_hkd > 0:
                            min_cap_hkd = min_market_cap * 1e8
                            max_cap_hkd = max_market_cap * 1e8
                            
                            if market_cap_hkd >= min_cap_hkd and market_cap_hkd <= max_cap_hkd:
                                stock = score_stock(data, settings, engine)
                                results.append(stock)
                    
                    # 避免請求過快
                    import time
                    time.sleep(0.3)
                
                status_text.text("分析完成！")
                progress_bar.empty()
                
                if results:
                    # 按評分排序
                    results.sort(key=lambda x: x.total_score, reverse=True)
                    
                    st.success(f"✅ 完成！共 {len(results)} 支股票符合條件")
                    
                    # Top N
                    top_results = results[:top_n]
                    
                    # 顯示結果表格
                    st.subheader(f"📊 Top {len(top_results)} 篩選結果")
                    
                    table_data = []
                    for s in top_results:
                        market_cap_hkd = s._raw_data.get('market_cap_hkd', 0) if hasattr(s, '_raw_data') else 0
                        score_emoji = get_score_color(s.total_score)
                        
                        table_data.append({
                            "代碼": s._raw_data.get('display_symbol', s.symbol.replace('.HK','')) if hasattr(s, '_raw_data') else s.symbol,
                            "名稱": s.name[:15],
                            "總評分": f"{s.total_score:.1f} {score_emoji}",
                            "市值": format_hkd(market_cap_hkd) if market_cap_hkd > 0 else "N/A",
                            "💰現價": f"HK${s.current_price:.2f}" if s.current_price else "N/A",
                            "FCF%": f"{s.fcf_yield*100:.1f}%",
                            "Beta": f"{s.beta:.2f}",
                            "52W位": f"{s.price_to_52w_low:.2f}"
                        })
                    
                    df_results = pd.DataFrame(table_data)
                    st.dataframe(df_results, use_container_width=True, hide_index=True)
                    
                    # 下載 CSV
                    csv_data = []
                    for s in top_results:
                        market_cap_hkd = s._raw_data.get('market_cap_hkd', 0) if hasattr(s, '_raw_data') else 0
                        csv_data.append({
                            '代碼': s._raw_data.get('display_symbol', s.symbol.replace('.HK','')) if hasattr(s, '_raw_data') else s.symbol,
                            '名稱': s.name,
                            '總評分': round(s.total_score, 1),
                            '市值(億港幣)': round(market_cap_hkd / 1e8, 2) if market_cap_hkd > 0 else 0,
                            '現價(HKD)': s.current_price,
                            '市值分': round(s.market_cap_score, 1),
                            '價值分': round(s.value_score, 1),
                            '現金流分': round(s.cash_flow_score, 1),
                            '低位分': round(s.price_position_score, 1),
                            '平衡分': round(s.balance_score, 1),
                            '利率敏感度分': round(s.rate_sensitivity_score, 1),
                            'Book-to-Market': round(s.book_to_market, 3),
                            'ROA(%)': round(s.roa * 100, 1),
                            'FCF Yield(%)': round(s.fcf_yield * 100, 1) if s.fcf_yield > 0 else 0,
                            'Beta': round(s.beta, 2),
                            '52W低位比率': round(s.price_to_52w_low, 2),
                        })
                    
                    df_csv = pd.DataFrame(csv_data)
                    csv_string = df_csv.to_csv(index=False).encode('utf-8-sig')
                    
                    st.download_button(
                        label="📥 下載 CSV",
                        data=csv_string,
                        file_name=f"港股十倍股篩選_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("沒有找到符合條件的股票，請嘗試擴大市值範圍。")


if __name__ == "__main__":
    main()
