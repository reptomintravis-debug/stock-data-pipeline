import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# 対象10銘柄
TICKERS = [
    '8035.T',  # 東京エレクトロン
    '4186.T',  # 東京応化工業
    '5803.T',  # フジクラ
    '6508.T',  # 明電舎
    '6504.T',  # 富士電機
    '5016.T',  # JX金属
    '6920.T',  # レーザーテック
    '6857.T',  # アドバンテスト
    '5801.T',  # 古河電工
    '5802.T',  # 住友電工
]

CSV_PATH = 'adjusted_ohlc_daily_prices.csv'

# Date + 10銘柄 × OHLC = 41列
COLUMNS = ['Date']

for ticker in TICKERS:
    code = ticker.split('.')[0]
    COLUMNS.extend([
        f'{code}_Open',
        f'{code}_High',
        f'{code}_Low',
        f'{code}_Close'
    ])


def main():

    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return

    # --------------------------------------------------
    # 1. 既存CSVを読み込む
    # --------------------------------------------------

    df_existing = pd.read_csv(CSV_PATH)

    # Date列を正規化
    df_existing['Date'] = pd.to_datetime(
        df_existing['Date'],
        errors='coerce'
    ).dt.strftime('%Y-%m-%d')

    # Dateが読めない行を削除
    df_existing = df_existing.dropna(subset=['Date'])

    # --------------------------------------------------
    # 2. 既存CSVを「正規の41列」に整理する
    #    余計な Ticker / Volume 等はここで完全に除去
    # --------------------------------------------------

    for col in COLUMNS:
        if col not in df_existing.columns:
            df_existing[col] = None

    df_existing = df_existing[COLUMNS]

    # Date重複があれば最後の行を残す
    df_existing = (
        df_existing
        .drop_duplicates(subset=['Date'], keep='last')
        .sort_values('Date')
        .reset_index(drop=True)
    )

    # --------------------------------------------------
    # 3. 最新日を確認
    # --------------------------------------------------

    last_date = pd.to_datetime(df_existing['Date'].max())

    # 最新日を含めて取得する
    # （既存データの最新日を再取得しても後で重複排除する）
    start_date = last_date.strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"Last date in CSV: {last_date.strftime('%Y-%m-%d')}")
    print(f"Fetching range: {start_date} to {end_date}")

    # --------------------------------------------------
    # 4. 10銘柄のデータ取得
    # --------------------------------------------------

    all_dates_data = {}

    for ticker in TICKERS:

        code = ticker.split('.')[0]

        try:
            print(f"Fetching {ticker}...")

            df_t = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                auto_adjust=True,
                progress=False
            )

            if df_t.empty:
                print(f"  No data: {ticker}")
                continue

            # yfinanceのMultiIndex対策
            if isinstance(df_t.columns, pd.MultiIndex):
                df_t.columns = df_t.columns.get_level_values(0)

            for idx, row in df_t.iterrows():

                date_str = idx.strftime('%Y-%m-%d')

                if date_str not in all_dates_data:
                    all_dates_data[date_str] = {
                        'Date': date_str
                    }

                all_dates_data[date_str][f'{code}_Open'] = (
                    round(float(row['Open']), 2)
                    if pd.notna(row['Open']) else None
                )

                all_dates_data[date_str][f'{code}_High'] = (
                    round(float(row['High']), 2)
                    if pd.notna(row['High']) else None
                )

                all_dates_data[date_str][f'{code}_Low'] = (
                    round(float(row['Low']), 2)
                    if pd.notna(row['Low']) else None
                )

                all_dates_data[date_str][f'{code}_Close'] = (
                    round(float(row['Close']), 2)
                    if pd.notna(row['Close']) else None
                )

        except Exception as e:
            print(f"Error fetching {ticker}: {e}")

    # --------------------------------------------------
    # 5. 新規データがなければ終了
    # --------------------------------------------------

    if not all_dates_data:
        print("No new data fetched.")
        return

    # --------------------------------------------------
    # 6. 新規データを41列に統一
    # --------------------------------------------------

    df_new = pd.DataFrame(list(all_dates_data.values()))

    for col in COLUMNS:
        if col not in df_new.columns:
            df_new[col] = None

    df_new = df_new[COLUMNS]

    # --------------------------------------------------
    # 7. 既存データ＋新規データを結合
    # --------------------------------------------------

    df_final = pd.concat(
        [df_existing, df_new],
        ignore_index=True
    )

    # Dateで重複排除
    # 新しく取得したデータを優先
    df_final = (
        df_final
        .drop_duplicates(subset=['Date'], keep='last')
        .sort_values('Date')
        .reset_index(drop=True)
    )

    # --------------------------------------------------
    # 8. Dateを正規化
    # --------------------------------------------------

    df_final['Date'] = pd.to_datetime(
        df_final['Date']
    ).dt.strftime('%Y-%m-%d')

    # --------------------------------------------------
    # 9. 最終的に41列だけを保存
    # --------------------------------------------------

    df_final = df_final[COLUMNS]

    df_final.to_csv(
        CSV_PATH,
        index=False
    )

    print()
    print("Successfully updated.")
    print(f"Total rows: {len(df_final)}")
    print(f"Total columns: {len(df_final.columns)}")
    print(f"Expected columns: {len(COLUMNS)}")


if __name__ == '__main__':
    main()