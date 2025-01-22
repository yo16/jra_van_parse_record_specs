"""
JRA-VANのデータ仕様書を拡張した「拡張フォーマット.xlsx」を、JSONオブジェクトに変換する main関数
"""

import pandas as pd
import json

from .split_by_record_format import split_by_record_format
from .parse_record_format import parse_record_format



def main(in_file_path, sheet_name, out_file_path):
    # ファイルを読み込む
    df = pd.read_excel(in_file_path, sheet_name=sheet_name, header=None)

    # dfをレコードフォーマットごとに分割し、それぞれのDataFrameオブジェクトを配列にする
    dfs = split_by_record_format(df)

    # それぞれのDataFrameをオブジェクトに変換し、全体のオブジェクトへ格納する
    records = {}
    for df in dfs:
        # １つのレコードフォーマットを、オブジェクトに変換する
        record_format = parse_record_format(df)

        # レコードフォーマットごとに、オブジェクトを格納する
        records[record_format["header"]["record_type_id"]] = record_format
    
    # ファイル出力
    pretty_json = json.dumps(records, indent=4, ensure_ascii=False)
    with open(out_file_path, "w", encoding="utf-8") as f:
        f.write(pretty_json)

    return



if __name__ == "__main__":
    main()

