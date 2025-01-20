"""
./data/recordFormat.jsonを読み、日本語に対する英語を取得する
"""

import json


# メイン
def main():
    # 入力ファイル
    input_file = "./data/recordFormat.json"
    # 出力ファイル
    output_file = "./data/transData.txt"

    # データを読み込む
    trans_data = get_trans_data(input_file)
    #print(trans_data)

    with open(output_file, "w", encoding="utf-8") as f:
        # すべてのrecordTypeIdについて、テーブル名(recordTypeNameJpとrecordTypeName)を取得する
        f.write(f"-- table name\n")
        for recordTypeId in trans_data:
            #print(recordTypeId)
            jp = trans_data[recordTypeId]["format_name_jp"]
            en = trans_data[recordTypeId]["format_name_en"]
            # ファイルへ出力
            f.write(convert_to_output_format(jp, en))
        
        # テーブルごとのcolumnsについて、列名(columnNameJpとcolumnName)を取得する
        f.write(f"-- column name\n")
        for recordTypeId in trans_data:
            for column in trans_data[recordTypeId]["columns"]:
                jp = column["column_name_jp"]
                en = column["column_name_en"]
                # ファイルへ出力
                f.write(convert_to_output_format(jp, en))

        # テーブルごとのcolumnsごとのsubColumnsInfoについて、列名(subColumnsInfo.columnNameJpとsubColumnsInfo.columnName)を取得する
        f.write(f"-- sub column name\n")
        for recordTypeId in trans_data:
            for column in trans_data[recordTypeId]["columns"]:
                if "sub_columns_info" in column:
                    for subColumn in column["sub_columns_info"]["sub_columns"]:
                        jp = subColumn["column_name_jp"]
                        en = subColumn["column_name_en"]
                        # ファイルへ出力
                        f.write(convert_to_output_format(jp, en))


# JPとENの文字列から、出力フォーマットに変換する
def convert_to_output_format(jp, en):
    return f"{jp}\t{en}\n"


# データを読み込む
def get_trans_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data





if __name__=="__main__":
    main()
