# jra_van_parse_record_specs
JRA-VANのデータ定義書（Excel）を読み、プログラミングで利用可能なJSONにする

## 全体概要
- JRA-VANのデータ定義書（JV-Data 仕様書Excel版（Ver.4.9.0.1）.xlsx）を読み、プログラミングで利用可能なJSON（`./data/recordFormat.json`）にする
- その際、不足しているデータは、手入力で補充する
- 補充した結果のファイルは、`./data/拡張フォーマット.xlsx`に保存する

## 手順
1. `./data/JV-Data 仕様書Excel版（Ver.4.9.0.1）.xlsx`を入手する
2. 拡張フォーマットにコピーし、W列より右を埋める
   - Google Spreadsheetで編集し、Excel形式でエクスポート
   - エクスポートしたファイルを`./data/拡張フォーマット.xlsx`に保存
3. カレントディレクトリが`jra_van_parse_record_specs`の状態で、`./src/create_record_format_json.py`を実行する
4. `./data/recordFormat.json`が生成される





