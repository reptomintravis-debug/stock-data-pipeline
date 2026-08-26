import pandas as pd
import yfinance as yf

CSV_PATH = 'adjusted_ohlc_daily_prices.csv'

# CSV読み込み
df = pd.read_csv(CSV_PATH)

# 新規2銘柄のデータ取得（2025-03-03以降）
start_date = '2025-03-03'
new_tickers = ['5801.T', '5802.T']

print("Fetching historical data for 5801.T and 5802.T...")
data = yf.download(new_tickers, start=start_date, interval='1d')

# 日付フォーマット調整
df['Date'] = pd.to_datetime(df['Date'])

for ticker_code in ['5801', '5802']:
    yf_symbol = f"{ticker_code}.T"
    
    # yfinanceデータから各値を取り出してマップ
    for col in ['Open', 'High', 'Low', 'Close']:
        col_name = f"{ticker_code}_{col}"
        
        # Seriesを作成して日付キーでマッピング
        series = data[col][yf_symbol]
        series.index = pd.to_datetime(series.index)
        
        # 既存DataFrameの空欄列を補完
        df[col_name] = df['Date'].map(series)

# 日付を文字列に戻して保存
df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
df.to_csv(CSV_PATH, index=False)
print("Backfill completed successfully.")
