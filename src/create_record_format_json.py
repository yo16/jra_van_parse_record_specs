"""
./data/拡張フォーマット.xlsxを読み、./data/recordFormat.jsonを生成する
"""

import os
import numpy as np
import pandas as pd
import re
import copy
import json


def main():
    # 入力ファイル
    input_file = os.path.join(os.path.dirname(__file__), "../data/拡張フォーマット.xlsx")
    # 出力ファイル
    output_file = os.path.join(os.path.dirname(__file__), "../data/recordFormat.json")

    # 拡張フォーマットを読み込む
    df = pd.read_excel(
        input_file,
        sheet_name="フォーマット4901",
        header=None
    )
    #print(df[:20]);
    
    # W列が"RECORD_DEFINITION"の行を探す
    record_definition_list = df[df.iloc[:, convert_to_index("W")] == "RECORD_DEFINITION"]
    #print(record_definition_list)

    # データ範囲（複数）を設定
    # データ範囲は、record_definition_listの行から、次のRECORD_DEFINITIONまたは末尾までを、データ範囲として設定する
    record_regions = []
    prev_start = 0
    for index, _ in record_definition_list.iterrows():
        current_index = int(index)

        if prev_start == 0:
            # indexを整数型に変換して格納
            prev_start = current_index
            continue

        record_regions.append({"start": prev_start, "end": current_index - 1})
        prev_start = current_index
    record_regions.append({"start": prev_start, "end": df.shape[0]})
    #print(record_regions)

    # 出力用のオブジェクトを定義
    record_format = {};

    # データ範囲ごとに、record_formatへ格納する
    for record_region in record_regions:
        start = record_region["start"]
        end = record_region["end"]

        regist_record_format(record_format, df.iloc[start:end])

    #print("--------------------------------")
    #print(record_format)
    pretty_json = json.dumps(record_format, indent=4, ensure_ascii=False)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty_json)
    
    print("finished")




# 引数で渡されたdfのレコードフォーマットを登録する
def regist_record_format(record_format, df):
    # 登録するオブジェクト
    record_format_object = {}

    # 全体の情報
    record_type_id = df.iloc[0][convert_to_index("AB")]
    print(record_type_id)
    format_number = convert_to_integer(df.iloc[0][convert_to_index("X")])
    format_name_jp = df.iloc[0][convert_to_index("Y")]
    format_name_en = df.iloc[0][convert_to_index("Z")]
    total_bytes = df.iloc[0][convert_to_index("AA")]

    # 列ごと（columnsプロパティ）の情報
    all_columns_objects = []
    cur_column_object = {}
    now_repeating = False   # 複数行にわたって繰り返すとき、前の行でTrueにする
    df_row_index = -1   # pandasのindexではなく、一般的な意味での行番号
    for _, row in df.iterrows():
        df_row_index += 1
        # ヘッダーをスキップ
        if df_row_index < 2:
            continue

        # 基本項目を抽出
        cur_item = extract_item(row)
        tmp = 1

        # seqもsub_seqも空の場合は、スキップ
        if (cur_item["seq"] == "") and (cur_item["sub_seq"] == ""):
            continue

        # 項目名が空の場合は、スキップ
        if cur_item["column_name_jp"] == "":
            continue

        # 型の定義がない、かつ、項目名が"<"で始まらない場合は、スキップ
        # （DBに取り込まない、かつ、繰り返しの指示行でもないという意味）
        if (cur_item["db_info"]["db_column_type"] == "") and (cur_item["column_name_jp"][0] != "<"):
            continue

        # repatingだけど、sub_seqが空の場合は、repeatingを終了
        # （繰り返し指示が終わって、次の項目に入ったという意味）
        if now_repeating and (cur_item["sub_seq"] == ""):
            # 前のrepeatingでに作っていたcur_column_object（繰り返し項目のはず）を、all_columns_objectsに追加
            all_columns_objects.append(cur_column_object)

            # 繰り返し項目の終了
            now_repeating = False
            cur_column_object = {}
        
        # 繰り返しパターンの判別
        if ("repeats" in cur_item) and (cur_item["repeats"] > 0):
            if cur_item["column_name_jp"][0] == "<":
                # 1. 項目名が<.*>で、その行のsub-seqは空で次の行以降のsub-seqがある場合、次の行からsub-seqを繰り返す
                now_repeating = True
                cur_column_object = cur_item
                cur_column_object["sub_columns_info"] = {
                    "repeats": cur_item["repeats"],
                    "sub_columns": []
                }
                # sub_columns_infoを作るときは、その内部にrepeatsを持つので、自身のrepeatsは削除する
                del cur_column_object["repeats"]

            elif (cur_item["sub_seq"] == "") or \
                ((cur_item["sub_seq"] != "") and (cur_item["seq"] == "") and now_repeating):
                # 2. repeatsがあり、項目名は通常通りの場合、１項目だけを繰り返す
                #   2.1. トップレベルの項目が、１項目で繰り返すパターン＝sub-seqが空の場合
                #       - レース詳細(RA)の項番40など
                #   2.2. 上記のパターン1.の繰り返しの中で、さらに１項目で繰り返すパターン
                #       - 騎手マスタ(KS)の項番24-fなど
                #       - この場合は入れ子になる
                # ここでの変数
                #   - トップレベルの項目: cur_column_object
                #   - 繰り返す項目: cur_sub_column_object

                # 繰り返す項目を作成（sub_column１つの単位に変更）
                parent_seq = cur_item["seq"] if cur_item["seq"] != "" else cur_column_object["seq"]
                cur_sub_column_object = copy.deepcopy(cur_item)
                cur_sub_column_object["seq"] = parent_seq
                del cur_sub_column_object["repeats"]
                cur_sub_column_object["bytes_total"] = cur_sub_column_object["bytes"]

                if now_repeating:
                    # 2.2.のパターン
                    # cur_sub_column_objectに、sub_sub_column_objectを作成する
                    cur_sub_sub_column_object = copy.deepcopy(cur_item)     # 同じ項目をさらに内側に作る
                    cur_sub_sub_column_object["seq"] = parent_seq
                    parent_sub_seq = cur_sub_column_object["sub_seq"]
                    cur_sub_sub_column_object["sub_seq"] = f"{parent_sub_seq},a"  # 2重に繰り返すので、a,aの形式とする
                    del cur_sub_sub_column_object["repeats"]
                    cur_sub_column_object["sub_columns_info"] = {
                        "repeats": cur_item["repeats"],
                        "sub_columns": [cur_sub_sub_column_object]
                    }
                    cur_sub_column_object["bytes_total"] = cur_sub_column_object["bytes"] * cur_item["repeats"]
                    cur_sub_sub_column_object["bytes_total"] = cur_sub_sub_column_object["bytes"]

                    # 繰り返し中の場合は、すでにcur_column_object["sub_columns_info"]["sub_columns"]があるので、その中にcur_sub_column_objectを追加する
                    cur_column_object["sub_columns_info"]["sub_columns"].append(cur_sub_column_object)

                else:
                    # 2.1.のパターン
                    # 繰り返し中ではない場合は、cur_column_objectを作成する
                    cur_sub_column_object["sub_seq"] = "a"  # 1つしかないので固定で"a"とする
                    # sub_columns_infoを作成
                    cur_column_object = copy.deepcopy(cur_item)
                    cur_column_object["seq"] = parent_seq
                    cur_column_object["sub_columns_info"] = {
                        "repeats": cur_item["repeats"],
                        "sub_columns": [cur_sub_column_object]
                    }
                    # sub_columns_infoを作るときは、その内部にrepeatsを持つので、自身のrepeatsは削除する
                    del cur_column_object["repeats"]

                    # columns_objectsに追加
                    all_columns_objects.append(cur_column_object)

                # 次の行の項目へ移る
                continue

        # repeatsは設定されていないが、繰り返し中の場合
        elif now_repeating:
            # 繰り返し中の場合は、すでにcur_column_object["sub_columns_info"]["sub_columns"]があるので、その中にcur_itemを追加する
            cur_item["seq"] = cur_column_object["seq"]
            cur_column_object["sub_columns_info"]["sub_columns"].append(
                cur_item
            )

        # 繰り返し中ではない場合
        else:
            all_columns_objects.append(cur_item)
    # 最後の項目が繰り返し項目の場合、まだ登録されていないので、その項目を追加
    if now_repeating:
        all_columns_objects.append(cur_column_object)

    # フォーマットに登録（引数に設定）
    record_format_object["record_type_id"] = record_type_id
    record_format_object["format_name_jp"] = format_name_jp
    record_format_object["format_name_en"] = format_name_en
    record_format_object["format_number"] = format_number
    record_format_object["total_bytes"] = total_bytes
    record_format_object["columns"] = all_columns_objects
    record_format[record_type_id] = record_format_object



# レコードから項目を抽出し、オブジェクトにして返す
def extract_item(row):
    seq = get_value(row[convert_to_index("B")], row[convert_to_index("B")], "")
    sub_seq = get_value(row[convert_to_index("C")], row[convert_to_index("C")], "")
    is_pk = get_value(row[convert_to_index("D")], True, False)
    column_name_jp = get_value(row[convert_to_index("E")], row[convert_to_index("E")], "")
    column_name_jp = re.sub(r'^　+', '', column_name_jp)
    column_name_en = get_value(row[convert_to_index("W")], row[convert_to_index("W")], "")  
    # カッコ書きでスペースにパディングされている場合は、そのカッコを削除して整数へ変換する
    start_pos_str = get_value(row[convert_to_index("F")], row[convert_to_index("F")], "0")
    start_pos = int(re.sub(r'[\(\)\s]', '', str(start_pos_str)))
    bytes = int(get_value(row[convert_to_index("H")], row[convert_to_index("H")], "0"))
    repeats = int(get_value(row[convert_to_index("G")], row[convert_to_index("G")], "0"))
    # 定義書では「初期値」だが、伝わりづらいので単語を変える
    padding_character = str(get_value(row[convert_to_index("J")], row[convert_to_index("J")], ""))
    comment = get_value(row[convert_to_index("K")], row[convert_to_index("K")], "")
    # DB関連
    db_column_type = get_value(row[convert_to_index("X")], row[convert_to_index("X")], "")
    size1 = int(get_value(row[convert_to_index("Y")], row[convert_to_index("Y")], "0"))
    size2 = int(get_value(row[convert_to_index("Z")], row[convert_to_index("Z")], "0"))
    db_column_length = size1 if size2 == 0 else [size1, size2]

    #db_sub_table_pk = False if np.isnan(row[convert_to_index("AC")]) else True
    db_sub_table_pk = get_value(row[convert_to_index("AC")], True, False)
    db_column_notnull = get_value(row[convert_to_index("AA")], True, False)
    # 繰返対応方法
    repat_item_handling = get_value(
        row[convert_to_index("AB")],
        row[convert_to_index("AB")],
        ""
    )
    # bytes_totalは、bytesとrepeatsを用いて計算する
    if repeats > 0:
        bytes_total = bytes * repeats
    else:
        bytes_total = bytes
    # 繰返対応方法が横持ちで、サフィックスルールをカスタマイズしている場合の項目
    repeat_suffix_rule = get_value(row[convert_to_index("AD")], row[convert_to_index("AD")], "")


    retObj = {
        "seq": seq,
        "sub_seq": sub_seq,
        "is_pk": is_pk,
        "column_name_jp": column_name_jp,
        "column_name_en": column_name_en,
        "start_pos": start_pos,
        "repeats": repeats,
        "bytes": bytes,
        "bytes_total": bytes_total,
        "padding_character": padding_character,
        "comment": comment,
        "db_info": {
            "db_column_type": db_column_type,
            "db_column_length": db_column_length,
            "db_sub_table_pk": db_sub_table_pk,
            "db_column_notnull": db_column_notnull
        }
    }

    # 繰返対応方法が設定されている場合は、繰り返し用の情報を追加
    if repat_item_handling != "":
        retObj["repat_item_handling"] = repat_item_handling
    # サフィックスルールが設定されている場合は、繰り返し用の情報を追加
    if repeat_suffix_rule != "":
        retObj["repeat_suffix_rule"] = repeat_suffix_rule
    
    # repeatsが0の場合は、"repeats"を削除
    if repeats == 0:
        del retObj["repeats"]

    return retObj



# Dataframeの値が、空の場合の値とそうでない場合の値を取得
# 引数はあえて、必ず指定する
def get_value(value, if_not_empty, if_empty):
    if isinstance(value, float) and np.isnan(value):
        return if_empty
    elif isinstance(value, str) and value == "":
        return if_empty
    else:
        return if_not_empty



# 全角の数字を整数へ変換する
def convert_to_integer(value):
    return int(value.replace("０", "0").replace("１", "1").replace("２", "2").replace("３", "3").replace("４", "4").replace("５", "5").replace("６", "6").replace("７", "7").replace("８", "8").replace("９", "9"))



# 列名のアルファベットから、indexの整数へ変換する
# 列名は、A、B、C、...、Y、Z、AA、AB、... となっている
# ２文字以上になった場合の考慮が重要
def convert_to_index(column_name):
    column_name = column_name.upper()  # 小文字対応のため大文字に変換
    index = 0
    for char in column_name:
        # Aを1、Bを2、...とする計算
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1  # Aが0になるように調整



if __name__ == "__main__":
    main()
