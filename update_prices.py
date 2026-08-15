import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# 1. 銘柄コードの定義 (JPXインデックス準拠)
TICKERS = {
    '1306': '1306.T', # TOPIX ETF
    '1540': '1540.T', # 金価格連動型上場投信
    '2516': '2516.T', # 東証マザーズETF
    '4186': '4186.T', # 東京応化工業
    '5016': '5016.T', # JX金属
    '6324': '6324.T', # ハーモニック・ドライブ・システムズ
    '6857': '6857.T', # アドバンテスト
    '6920': '6920.T'  # レーザーテック
}

CSV_FILE = 'adjusted_ohlc_daily_prices.csv'

def main():
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"{CSV_FILE} が見つかりません。")

    # 既存データの読み込み
    df_existing = pd.read_csv(CSV_FILE)
    df_existing['Date'] = pd.to_datetime(df_existing['Date'])

    # 最新の日付を取得
    last_date = df_existing['Date'].max()
    start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    if start_date > end_date:
        print("最新データは既に取得済みです。")
        return

    print(f"{start_date} から {end_date} までのデータを取得中...")

    # 新規データの取得
    new_data_list = []
    for symbol, yf_ticker in TICKERS.items():
        try:
            ticker = yf.Ticker(yf_ticker)
            df_ticker = ticker.history(start=start_date, end=end_date)
            
            if not df_ticker.empty:
                df_ticker = df_ticker.reset_index()
                df_ticker['Ticker'] = int(symbol)
                # 調整後終値を考慮したOHLCの取得
                df_ticker = df_ticker[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
                df_ticker['Date'] = pd.to_datetime(df_ticker['Date']).dt.strftime('%Y-%m-%d')
                new_data_list.append(df_ticker)
        except Exception as e:
            print(f"銘柄 {symbol} の取得エラー: {e}")

    if not new_data_list:
        print("新規に取得できるデータがありませんでした。")
        return

    # データの結合と整理
    df_new = pd.concat(new_data_list, ignore_index=True)
    df_new['Date'] = pd.to_datetime(df_new['Date'])

    # 既存データと統合して重複排除
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['Date', 'Ticker'], keep='last')
    
    # 昇順ソート
    df_combined = df_combined.sort_values(by=['Date', 'Ticker']).reset_index(drop=True)
    df_combined['Date'] = df_combined['Date'].dt.strftime('%Y-%m-%d')

    # CSVへの保存
    df_combined.to_csv(CSV_FILE, index=False)
    print("CSVの更新が完了しました。")

if __name__ == '__main__':
    main()
