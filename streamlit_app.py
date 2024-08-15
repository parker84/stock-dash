import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import coloredlogs, logging
logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO', logger=logger)
todays_date = datetime.now().date()

st.set_page_config(page_title="Stocks Dashboard", layout="wide", page_icon="🔻")
st.title("🔻 Stocks Dashboard")
st.caption("A better way to monitor your favourite stocks 📊")
st.logo("assets/TorCrime_logo.png")


# --------------constants
DEFAULT_STOCK_SYMBOLS = ["NVDA", "META", "AMZN", "MSFT", "SHOP", "TSLA", "AAPL"]
DAYS_BACK = [1, 7, 30,90, 180, 365]
CHANGE_ICONS = {
    'Big Negative Drop < -10%': '📉',
    'Small Negative Drop [-1%, 10%]': '🔻',
    'Neutral Change (-1%, 1%)': '',
    'Small Positive Rise [1%, 10%]': '🟢',
    'Big Positive Rise > 10%': '🚀',
}

# --------------helpers
@st.cache_data()
def get_sp500_tickers(todays_date):
    logger.info(f'🏃 Fetching S&P 500 tickers - {todays_date}')
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url)
    df = table[0]
    sp500_tickers = df['Symbol'].tolist()    
    logger.info(f'✅ Fetched S&P 500 tickers - {todays_date}')
    return sp500_tickers

@st.cache_data()
def get_data_for_stocks(stock_symbols, start_date, end_date):
    logger.info(f'🏃 Fetching data for {stock_symbols} - {start_date} to {end_date}')
    stock_data = yf.download(stock_symbols, start=start_date, end=end_date)
    logger.info(f'✅ Fetched data for {stock_symbols} - {start_date} to {end_date}')
    stock_data.sort_values(by=['Date'], inplace=True)
    return stock_data

def get_pct_changes(stock_data, days_back):
    pct_changes = {}
    for days_back in DAYS_BACK:
        pct_changes[days_back] = stock_data['Adj Close'].pct_change(days_back, fill_method=None)
    return pct_changes

def test_pct_changes(stock_data, pct_changes, days_back):
    for days_back in DAYS_BACK:
        expected_pct_change = (stock_data['Adj Close'].iloc[-1] / stock_data['Adj Close'].iloc[-(days_back+1)]) - 1
        actual_pct_change = pct_changes[days_back].iloc[-1]
        equals = expected_pct_change == actual_pct_change
        assert int(equals.sum()) == len(equals), f"Expected {expected_pct_change}, got {actual_pct_change}"

# --------------parameters
tickers = get_sp500_tickers(todays_date) + ['SHOP', 'AAPL']

start_date = st.sidebar.date_input("Start Date", value=datetime.now() - timedelta(days=365*5))
end_date = st.sidebar.date_input("End Date", value=todays_date)
st.sidebar.caption("Made with ❤️ by [Brydon](https://brydon.streamlit.app/)")

stock_symbols = st.multiselect(
    label="Stocks",
    default=DEFAULT_STOCK_SYMBOLS,
    options=tickers
)

stock_data = get_data_for_stocks(stock_symbols, start_date, end_date)
logger.info(f'stock_data_df: {stock_data}')
logger.info(f'stock_data columns: {stock_data.columns}')

logger.info('➗ Getting % Changes')
pct_changes = get_pct_changes(stock_data, DAYS_BACK)
logger.info('✅ Got % Changes')

logger.info('🧪 Testing % Changes')
test_pct_changes(stock_data, pct_changes, DAYS_BACK)
logger.info('✅ % Change Tests Passed')

logger.info('⚙️ Processing Data')
df_viz = stock_data['Adj Close'].iloc[[-1]].T
df_viz.columns = ['Adjusted Close Price']

for days_back in DAYS_BACK:
    df_viz[f'pct_change_{days_back}d'] = (pct_changes[days_back].iloc[-1] * 100).astype(float)
    color_coded = []
    for val in df_viz[f'pct_change_{days_back}d']:
        if val < 0:
            if val < -10:
                color_coded.append(CHANGE_ICONS['Big Negative Drop < -10%'])
            elif val <= -1:
                color_coded.append(CHANGE_ICONS['Small Negative Drop [-1%, 10%]'])
            else:
                color_coded.append(CHANGE_ICONS['Neutral Change (-1%, 1%)'])
        else:
            if val > 10:
                color_coded.append(CHANGE_ICONS['Big Positive Rise > 10%'])
            elif val >= 1:
                color_coded.append(CHANGE_ICONS['Small Positive Rise [1%, 10%]'])
            else:
                color_coded.append('')
    df_viz[f'pct_change_{days_back}d'] = [f"{val:.1f}% {emoji}" for val, emoji in zip(df_viz[f'pct_change_{days_back}d'], color_coded)]
logger.info('✅ Data Processed')

logger.info('📊 Visualizing Data')

pct_change_col_configs = {
    f'pct_change_{days}d': st.column_config.TextColumn(
        f"% Change ({days}d)",
    )
   for days in DAYS_BACK
}

col1, col2 = st.columns((3,1))

with col1:
    st.dataframe(
        df_viz,
        column_config=pct_change_col_configs,
        use_container_width=True,
    )
with col2:
    st.caption("**Legend**")
    for change, emoji in CHANGE_ICONS.items():
        st.caption(f"{emoji} = {change}")


col1, col2 = st.columns(2)
with col1:
    p = px.line(
        stock_data['Adj Close'],
        title=f"Daily Adjusted Close Prices",
        labels={"value": "Price", "Date": "Date"},
    )
    st.plotly_chart(p, use_container_width=True)

with col2:
    p = px.line(
        stock_data['Volume'],
        title=f"Daily Volume Traded",
        labels={"value": "Volume", "Date": "Date"},
    )
    st.plotly_chart(p, use_container_width=True)

logger.info('✅ Data Visualized')

logger.info('🏁 Done')