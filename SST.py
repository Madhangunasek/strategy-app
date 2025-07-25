import yfinance as yf
import pandas as pd
# Step 1: Load tickers from CSV file (must have a column named 'Ticker')
tickers_df = pd.read_csv("/content/drive/MyDrive/Stock Signal System/Stock_data.csv")  # Make sure stocks.csv exists in the same folder
tickers = tickers_df['Instrument'].tolist()
all_results = []
for ticker in tickers:
    ticker=ticker+".NS"  # Append exchange suffix for NSE stocks
    print(f"Processing {ticker}...")
    stock = yf.Ticker(ticker)

    # Get 1-year daily data
    df = stock.history(period="1y", interval="1d", auto_adjust=False)

    if df.empty:
        print(f"⚠️ No data for {ticker}, skipping.")
        continue

    # Clean and prepare
    df.reset_index(inplace=True)
    df['Date'] = df['Date'].dt.tz_localize(None)  # ❗️ Remove timezone for Excel compatibility
    df = df[['Date', 'High', 'Low']]
    df[['High', 'Low']] = df[['High', 'Low']].round(2)

    # 20-day High and Low
    df['20D_High'] = df['High'].rolling(window=20).max().round(2)
    df['20D_Low'] = df['Low'].rolling(window=20).min().round(2)

    # Trigger and Signal logic
    df['Trigger'] = (df['Low'] <= df['20D_Low']).astype(int)
    df['Signal'] = ""
    df['State'] = 0

    for i in range(1, len(df)):
        if df.loc[i, 'Trigger'] == 1:
            df.loc[i, 'Signal'] = "start"
            df.loc[i, 'State'] = 1
        elif df.loc[i - 1, 'State'] == 1 and df.loc[i, 'High'] >= df.loc[i, '20D_High']:
            df.loc[i, 'Signal'] = "signal"
            df.loc[i, 'State'] = 0
        elif df.loc[i - 1, 'State'] == 1:
            df.loc[i, 'Signal'] = "wait"
            df.loc[i, 'State'] = 1

    # Add ticker column
    df['Ticker'] = ticker

    # Append last 30 rows (or full df if needed)
    all_results.append(df.tail(30))
    final_df = pd.concat(all_results, ignore_index=True)
    import math



# Step 6: Extract last 'signal' per stock
signal_summary = (
    final_df[final_df['Signal'] == "signal"]
    .groupby('Ticker')
    .apply(lambda x: x.sort_values('Date').iloc[-1])
    .reset_index(drop=True)[['Ticker', 'Date', 'Signal']]
)
signal_summary.rename(columns={'Date': 'Last_Signal_Date'}, inplace=True)

# Step 7: Sort by latest signal date
signal_summary.sort_values(by='Last_Signal_Date', ascending=False, inplace=True)

# Step 8: Add extra columns
prices = []

for ticker in signal_summary['Ticker']:
    try:
        data = yf.download(ticker, period="2d", interval="1d", progress=False)
        if not data.empty:
            price = round(float(data['Close'].iloc[-1]), 2)
        else:
            price = None
        prices.append(price)
    except Exception as e:
        print(f"⚠️ Error fetching price for {ticker}: {e}")
        prices.append(None)

signal_summary['Price'] = prices

# Final column order (without Amount and QTY)
signal_summary = signal_summary[
    ['Ticker', 'Last_Signal_Date', 'Signal', 'Price']
]


# # --- Step 9: Export both sheets to Excel ---
# with pd.ExcelWriter("multi_stock_signals.xlsx", engine="openpyxl") as writer:
#     final_df.to_excel(writer, index=False, sheet_name="Full Signals")
#     signal_summary.to_excel(writer, index=False, sheet_name="Signal Summary")

# print("✅ Excel saved: 'multi_stock_signals.xlsx' with updated Signal Summary (no Amount/QTY).")
import math
import datetime

# Get today's date in the same format as the 'Date' column
today = datetime.date.today()

# Filter for rows where 'Signal' is "signal" and 'Date' is today's date
today_signals = (
    final_df[
        (final_df['Signal'] == "signal") &
        (final_df['Date'].dt.date == today)
    ]
    .groupby(['Ticker', final_df['Date'].dt.date])
    .apply(lambda x: x.sort_values('Date').iloc[-1])  # In case multiple entries exist per Ticker-date
    .reset_index(drop=True)
    [['Ticker', 'Date', 'Signal']]
)

# Clean up tickers: remove ".NS" and prepend "NSE:"
today_signals['Stock'] = today_signals['Ticker'].str.replace(".NS", "", regex=False).apply(lambda x: f"NSE:{x}")

today_signals.rename(columns={'Date': 'Today_Signal_Date'}, inplace=True)

# Step 7: Sort by latest signal date
today_signals.sort_values(by='Today_Signal_Date', ascending=False, inplace=True)

# Step 8: Add extra columns
prices = []

for ticker in today_signals['Ticker']:
    try:
        data = yf.download(ticker, period="2d", interval="1d", progress=False)
        if not data.empty:
            price = round(float(data['Close'].iloc[-1]), 2)
        else:
            price = None
        prices.append(price)
    except Exception as e:
        print(f"⚠️ Error fetching price for {ticker}: {e}")
        prices.append(None)

today_signals['Price'] = prices
today_signals['variety'] = 'regular'
today_signals['exchange'] = 'NSE'
today_signals['Transaction Type'] = 'BUY'
today_signals['Order Type'] = 'MARKET'
today_signals['Product'] = 'CNC'
today_signals['quantity'] = ''
today_signals['amount'] = ''
today_signals['Qty2'] = ''

# Final column order (without Amount and QTY)
Today_signal = today_signals[
    ['Today_Signal_Date', 'Ticker', 'Signal', 'Price', 'variety', 'exchange', 'Transaction Type', 'Order Type', 'Product', 'quantity', 'amount', 'Qty2']
]
print(Today_signal)
!pip install openpyxl
!pip install gspread gspread_dataframe oauth2client
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe
import pandas as pd

# Set up Google Sheets authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/content/drive/MyDrive/Stock Signal System/service_account.json", scope)
client = gspread.authorize(creds)

# Open spreadsheet
spreadsheet = client.open("Multi Stock Signals")

# 🟦 Sheet 1: Update "Full Signals"
worksheet1 = spreadsheet.sheet1
worksheet1.update_title("Full Signals")
set_with_dataframe(worksheet1, final_df)

# 🟨 Sheet 2: Rewrite "Signal Summary"
worksheet2 = spreadsheet.worksheet("Signal Summary")
worksheet2.clear()
set_with_dataframe(worksheet2, signal_summary)

# 🟧 Sheet 3: Preserve 'quantity', 'amount', 'Qty2' while updating rest
#worksheet3 = spreadsheet.worksheet("Today Signal")
#expected_headers = ['Today_Signal_Date', 'Ticker', 'Signal', 'Price', 'variety', 'exchange', 'Transaction Type', 'Order Type', 'Product']  # Add all relevant column headers
#worksheet3.clear()
#set_with_dataframe(worksheet3, Today_signal)
# 🟧 Sheet 3: Preserve 'quantity', 'amount', 'Qty2' row-by-row even if tickers change
worksheet3 = spreadsheet.worksheet("Today Signal")

# Step 1: Read current sheet data
existing_data = worksheet3.get_all_records()
existing_df = pd.DataFrame(existing_data)

# Step 2: If existing sheet has rows, preserve manual columns row by row
if not existing_df.empty and 'quantity' in existing_df.columns:
    # Get only the manual columns, as list
    manual_columns = existing_df[['quantity', 'amount', 'Qty2']].copy()

    # Trim manual column list to match today's length (if shorter or longer)
    manual_columns = manual_columns.reindex(index=range(len(Today_signal))).fillna('')

    # Replace the new auto-generated blanks with the old manual values
    Today_signal[['quantity', 'amount', 'Qty2']] = manual_columns

# Step 3: Reorder columns to desired format
final_today_signal = Today_signal[
    ['Today_Signal_Date', 'Ticker', 'Signal', 'Price', 'variety', 'exchange',
     'Transaction Type', 'Order Type', 'Product', 'quantity', 'amount', 'Qty2']
]

# Step 4: Update the sheet
worksheet3.clear()
set_with_dataframe(worksheet3, final_today_signal)

print("✅ Sheets updated: 'Full Signals', 'Signal Summary', and 'Today Signal' (with preserved columns) now live!")
