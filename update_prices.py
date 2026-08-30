import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# 1. 対象8銘柄の定義
TICKERS = ['8035.T', '4186.T', '5803.T', '6508.T', '6504.T', '5016.T', '6920.T', '6857.T', '5801.T', '5802.T']
CSV_PATH = 'adjusted_ohlc_daily_prices.csv'

# 2. 列構造（33列）の定義
COLUMNS = ['Date']
for ticker in TICKERS:
    code = ticker.split('.')[0]
    COLUMNS.extend([f'{code}_Open', f'{code}_High', f'{code}_Low', f'{code}_Close'])

def main():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return

    # 既存データ読込
    df_existing = pd.read_csv(CSV_PATH)
    df_existing['Date'] = pd.to_datetime(df_existing['Date'])
    last_date = df_existing['Date'].max()
    
    start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"Last date in CSV: {last_date.strftime('%Y-%m-%d')}")
    print(f"Fetching range: {start_date} to {end_date}")

    if start_date > end_date:
        print("Data is already up to date.")
        return

    # 銘柄ごとに個別に取得して日付キーで結合（マルチインデックス起因のエラー回避）
    all_dates_data = {}

    for ticker in TICKERS:
        code = ticker.split('.')[0]
        try:
            # 1銘柄ずつ取得
            df_t = yf.download(ticker, start=start_date, end=datetime.now() + timedelta(days=1), progress=False)
            if df_t.empty:
                continue

            # MultiIndexカラム対策
            if isinstance(df_t.columns, pd.MultiIndex):
                df_t.columns = df_t.columns.get_level_values(0)

            for idx, row in df_t.iterrows():
                date_str = idx.strftime('%Y-%m-%d')
               if date_str <= last_date.strftime('%Y-%m-%d'):
     continue

                if date_str not in all_dates_data:
                    all_dates_data[date_str] = {'Date': date_str}

                all_dates_data[date_str][f'{code}_Open'] = round(float(row['Open']), 2) if pd.notna(row['Open']) else None
                all_dates_data[date_str][f'{code}_High'] = round(float(row['High']), 2) if pd.notna(row['High']) else None
                all_dates_data[date_str][f'{code}_Low'] = round(float(row['Low']), 2) if pd.notna(row['Low']) else None
                all_dates_data[date_str][f'{code}_Close'] = round(float(row['Close']), 2) if pd.notna(row['Close']) else None

        except Exception as e:
            print(f"Error fetching {ticker}: {e}")

    if not all_dates_data:
        print("No new valid data fetched.")
        return

    # リスト化してDataFrameを作成
    new_rows = list(all_dates_data.values())
    df_new = pd.DataFrame(new_rows)

    # 不足列をNoneで補完しつつ、厳密に33列に揃える
    for col in COLUMNS:
        if col not in df_new.columns:
            df_new[col] = None

    df_new = df_new[COLUMNS]

    # 日付昇順ソート
    df_new = df_new.sort_values('Date').reset_index(drop=True)

    # 結合してCSV出力
    df_existing['Date'] = df_existing['Date'].dt.strftime('%Y-%m-%d')
    df_final = pd.concat([df_existing, df_new], ignore_index=True)
　　df_final = df_final.drop_duplicates(subset=['Date'], keep='first')
    df_final.to_csv(CSV_PATH, index=False)
    print(f"Successfully appended {len(df_new)} row(s).")

if __name__ == '__main__':
    main()
