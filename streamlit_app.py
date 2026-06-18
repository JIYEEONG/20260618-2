import datetime

import FinanceDataReader as fdr
import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Korea Stock Trend",
    page_icon="📈",
    layout="wide",
)

page_style = """
<style>
body {
    background: radial-gradient(circle at top left, rgba(0, 122, 255, 0.14), transparent 25%),
                radial-gradient(circle at bottom right, rgba(10, 132, 255, 0.08), transparent 20%),
                #f7f7f8;
}
section[data-testid='stAppViewContainer'] {
    background: transparent;
}
.reportview-container .main .block-container {
    padding-top: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}
.css-1d391kg {
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.7);
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.08);
    border-radius: 24px;
}
</style>
"""

st.markdown(page_style, unsafe_allow_html=True)

st.markdown("""
# 📈 국내 주식 가격 트렌드

Apple 스타일의 깔끔한 디자인으로 최근 국내 주식 가격을 확인하세요.
""")

with st.sidebar:
    st.header("조회 설정")
    stock_code = st.text_input("KRX 종목 코드", value="005930", max_chars=6)
    days = st.slider("조회 기간 (일)", min_value=10, max_value=180, value=60, step=10)
    start_date = st.date_input("시작일", value=datetime.date.today() - datetime.timedelta(days=days))
    refresh = st.button("데이터 새로고침")

@st.cache_data(show_spinner=False)
def load_stock_data(symbol: str, start: datetime.date) -> pd.DataFrame:
    symbol = symbol.strip()
    if not symbol:
        raise ValueError("유효한 종목 코드를 입력하세요.")
    data = fdr.DataReader(symbol, start=start)
    if data.empty:
        raise ValueError(f"{symbol}에 대한 데이터를 찾을 수 없습니다.")
    data = data.reset_index()
    data["Change"] = data["Close"].pct_change() * 100
    return data

try:
    with st.spinner("데이터를 불러오는 중입니다..."):
        stock = load_stock_data(stock_code, start_date)

    latest = stock.iloc[-1]
    prev = stock.iloc[-2] if len(stock) > 1 else latest
    change = latest.Close - prev.Close
    change_pct = (change / prev.Close) * 100 if prev.Close else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("현재가", f"{latest.Close:,.0f}원", delta=f"{change:+.0f}원")
    col2.metric("전일 대비", f"{change_pct:+.2f}%", delta=f"{change_pct:+.2f}%")
    col3.metric("거래일", latest.Date.strftime("%Y-%m-%d"), f"{len(stock)}일")

    st.markdown("---")
    st.subheader(f"{stock_code} 최근 가격 변화")

    line = alt.Chart(stock).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X("Date:T", title="날짜"),
        y=alt.Y("Close:Q", title="종가", axis=alt.Axis(format=",")),
        tooltip=[
            alt.Tooltip("Date:T", title="날짜"),
            alt.Tooltip("Close:Q", title="종가", format=","),
            alt.Tooltip("Volume:Q", title="거래량", format=","),
        ],
    ).properties(height=420)

    band = alt.Chart(stock).mark_area(opacity=0.14, interpolate="monotone", color="#0a84ff").encode(
        x="Date:T",
        y=alt.Y("Close:Q", stack=None),
    )

    st.altair_chart((band + line).configure_view(strokeOpacity=0), use_container_width=True)

    st.subheader("데이터 요약")
    st.dataframe(
        stock[["Date", "Open", "High", "Low", "Close", "Volume", "Change"]].assign(
            Date=stock["Date"].dt.strftime("%Y-%m-%d")
        ),
        use_container_width=True,
    )

    st.caption("FinanceDataReader를 사용하여 국내 주식 데이터를 가져옵니다. Apple 스타일의 미니멀 디자인을 지향합니다.")
except Exception as exc:
    st.error(str(exc))
    st.write("KRX 종목 코드를 입력하거나 네트워크 연결을 확인하세요.")
