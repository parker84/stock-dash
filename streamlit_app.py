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
DAYS_BACK = [1, 7, 30,90, 180] # TODO: 365d change doesn't work
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
    return stock_data


# --------------parameters
tickers = get_sp500_tickers(todays_date) + ['SHOP', 'AAPL']

start_date = st.sidebar.date_input("Start Date", value=datetime.now() - timedelta(days=370))
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

logger.info(f'🏃 Plotting data for {stock_symbols} - {start_date} to {end_date}')
# st.line_chart(stock_data['Adj Close'])

pct_changes = {}
for days_back in DAYS_BACK:
    # TODO: 365d change doesn't work
    pct_changes[days_back] = stock_data['Adj Close'].pct_change(days_back, fill_method=None)
# TODO: bring this into the dataframe

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

pct_change_col_configs = {
    # f'pct_change_{days}d': st.column_config.ProgressColumn(
    #     f"% Change ({days}d)",
    #     format="%.1f%%",
    #     width="medium",
    #     min_value=df_viz[f'pct_change_{days}d'].min(),
    #     max_value=df_viz[f'pct_change_{days}d'].max(),
    # )
    f'pct_change_{days}d': st.column_config.TextColumn(
        f"% Change ({days}d)",
        # format="%.1f%%",
        # width="medium",
        # min_value=df_viz[f'pct_change_{days}d'].min(),
        # max_value=df_viz[f'pct_change_{days}d'].max(),
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



# TODO: line chart for adj close (maybe market cap)
# TODO: better line chart for adj close
# TODO: pie chart for market cap

# TODO: include big metrics at the top + changes (every 30d?)

# TODO: email screenshots every week?


# TODO: table with change in last 30/365/7/1 days
# TODO: colour code the changes with emojis
# TODO: include the line charts in the table?


col1, col2 = st.columns(2)
with col1:
    p = px.line(
        stock_data['Adj Close'],
        title=f"Daily Adjusted Close Prices",
        labels={"value": "Price", "Date": "Date"},
    )
    # if stock_symbols == DEFAULT_STOCK_SYMBOLS:
    #     for symbol in DEFAULT_STOCK_SYMBOLS:
    #         if symbol not in ['AAPL', 'AMZN']:
    #             p.update_traces(visible="legendonly", selector=dict(name=symbol))
    st.plotly_chart(p, use_container_width=True)

with col2:
    p = px.line(
        stock_data['Volume'],
        title=f"Daily Volume Traded",
        labels={"value": "Volume", "Date": "Date"},
    )
    st.plotly_chart(p, use_container_width=True)