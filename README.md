# jra_van_parse_record_specs
JRA-VANのデータ定義書（Excel）を読み、プログラミングで利用可能なJSONにする

## 全体概要
- JRA-VANのデータ定義書（JV-Data 仕様書Excel版（Ver.4.9.0.1）.xlsx）を読み、プログラミングで利用可能なJSON（`./data/recordFormat.json`）にする
- その際、不足しているデータは、手入力で補充する
- 補充した結果のファイルは、`./data/拡張フォーマット.xlsx`に保存する

## 手順
1. `./data/JV-Data 仕様書Excel版（Ver.4.9.0.1）.xlsx`を入手する
2. 拡張フォーマットにコピーし、W列より右を埋める
   - Google Spreadsheetで編集し、エクスポートした実績しかない
3. `./create_record_format_json.py`を実行する
4. `./data/recordFormat.json`が生成される

## jsonファイルの利用方法
- DBのDDL作成
  - `./create_ddl.py`を実行する
- CSVを読み込み、DBへインポート




