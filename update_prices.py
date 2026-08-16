import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# 1. 対象8銘柄の厳格な定義
TICKERS = ['8035.T', '4186.T', '5803.T', '6508.T', '6504.T', '5016.T', '6920.T', '6857.T']
CSV_PATH = 'adjusted_ohlc_daily_prices.csv'

# 既存のCSV列定義（33列）
COLUMNS = ['Date']
for ticker in TICKERS:
    code = ticker.split('.')[0]
    COLUMNS.extend([f'{code}_Open', f'{code}_High', f'{code}_Low', f'{code}_Close'])

def main():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return

    # 既存データの読み込み
    df_existing = pd.read_csv(CSV_PATH)
    df_existing['Date'] = pd.to_datetime(df_existing['Date'])
    last_date = df_existing['Date'].max()
    
    start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    if start_date > end_date:
        print("Data is already up to date.")
        return

    print(f"Fetching data from {start_date} to {end_date}...")

    # Yahoo Financeからデータ取得
    data = yf.download(TICKERS, start=start_date, end=datetime.now() + timedelta(days=1), group_by='ticker')

    new_rows = []
    # 取得した日付のリストを取り出す
    dates = data.index.unique()

    for d in dates:
        date_str = d.strftime('%Y-%m-%d')
        if date_str <= last_date.strftime('%Y-%m-%d'):
            continue
        
        row_dict = {'Date': date_str}
        has_data = False

        for ticker in TICKERS:
            code = ticker.split('.')[0]
            try:
                if len(TICKERS) > 1:
                    df_ticker = data[ticker]
                else:
                    df_ticker = data

                if d in df_ticker.index:
                    open_val = df_ticker.loc[d, 'Open']
                    high_val = df_ticker.loc[d, 'High']
                    low_val = df_ticker.loc[d, 'Low']
                    close_val = df_ticker.loc[d, 'Close']

                    if pd.notna(close_val):
                        row_dict[f'{code}_Open'] = round(float(open_val), 2)
                        row_dict[f'{code}_High'] = round(float(high_val), 2)
                        row_dict[f'{code}_Low'] = round(float(low_val), 2)
                        row_dict[f'{code}_Close'] = round(float(close_val), 2)
                        has_data = True
                    else:
                        row_dict[f'{code}_Open'] = None
                        row_dict[f'{code}_High'] = None
                        row_dict[f'{code}_Low'] = None
                        row_dict[f'{code}_Close'] = None
                else:
                    row_dict[f'{code}_Open'] = None
                    row_dict[f'{code}_High'] = None
                    row_dict[f'{code}_Low'] = None
                    row_dict[f'{code}_Close'] = None
            except Exception as e:
                print(f"Error processing {ticker} for {date_str}: {e}")

        if has_data:
            new_rows.append(row_dict)

    if new_rows:
        df_new = pd.DataFrame(new_rows)
        # 厳格な33列の並び順を保証
        df_new = df_new.reindex(columns=COLUMNS)
        
        # 既存データと結合して書き出し
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        df_final['Date'] = df_final['Date'].dt.strftime('%Y-%m-%d')
        df_final.to_csv(CSV_PATH, index=False)
        print(f"Successfully appended {len(new_rows)} rows.")
    else:
        print("No new data to append.")

if __name__ == '__main__':
    main()
