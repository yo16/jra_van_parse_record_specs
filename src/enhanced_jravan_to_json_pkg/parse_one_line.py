"""
１行のデータを、オブジェクトに変換する
"""

import copy
import numpy as np
import pandas as pd
import re


from .utils import convert_to_index


# 行データをオブジェクトに変換する
# 引数:
#       row:    行データ
#       previous_column_info:
#               前回の列データ（デフォルトは空で、指定されたときはそこへ追加して返す）
# 戻り値:
#       column_info:
#               今回のrowに対する列名と列データ
#       final_previous_column_info:
#               確定した前回の列データ。
#               引数にprevious_column_infoが指定され、戻り値が0か1のときに設定される。
#       line_status: 読み込んだ行の状態
#                0: 今回のrowを、新しい行として１列の情報を読み込んだ
#                1: 次に続く可能性があるため、次回呼び出し時は今回の戻り値を引数に与える必要あり
#               -1: 空行などで、データとしては不要。エラーではなく、スキップする。
#               -9: エラー
def parse_one_line(row, previous_column_info=None):

    # 単純に、rowをオブジェクトに変換する
    simple_obj = parse_one_line_simple(row)

    # 使用すべき行であるか、スキップするかを確認する
    if not is_valid_line(simple_obj):
        return previous_column_info, None, -1
    
    # 入力チェック
    if not check_input(simple_obj):
        return None, None, -9
    
    # 型の変換
    basic_obj = convert_to_basic_obj(simple_obj)
    
    # 前回の列データの処理
    # previous_column_infoが指定されている場合、
    # 今回のrowが、前回のrowの続きであるかを確認する
    ret_final_previous_column_info = None
    if previous_column_info is not None:
        # sub_seqが空の場合は、続きではなく、前回で終了が確定
        if basic_obj["sub_seq"] == "":
            ret_final_previous_column_info = previous_column_info
    
    # 今回の列データの処理
    ret_cur_column_info = None
    ret_line_status = 0
    # トップレベルの列かそうでないか
    if basic_obj["seq"] != 0:
        # トップレベルの列
        if basic_obj["repeats"] == 0:
            # repeatsが設定されていない
            # 単独列（ループなし）
            ret_cur_column_info = create_column_info_single_no_repeats(basic_obj)
            ret_line_status = 0

        elif (basic_obj["column_name_jp"] != "") and (basic_obj["column_name_jp"][0] != "<"):
            # repeatsが設定されていて、列名が"<"で始まらない
            # 単独列（ループあり）
            ret_cur_column_info = create_column_info_single_repeats(basic_obj)
            ret_line_status = 0

        else:
            # repeatsが設定されていて、列名が"<"で始まる
            # 複数ループ開始
            ret_cur_column_info = create_column_info_repeat_start(basic_obj)
            ret_line_status = 1

    else:
        # トップレベルの列ではない
        # この場合、previous_column_infoのsub_columnに追加する
        if basic_obj["repeats"] == 0:
            # repeatsが設定されていない
            # 単独列（ループなし）
            ret_cur_column_info = copy.deepcopy(previous_column_info)
            ret_cur_column_info["sub_columns_info"]["sub_columns"].append( \
                create_column_info_single_no_repeats(basic_obj, previous_column_info))
            ret_line_status = 1

        else:
            # repeatsが設定されている
            # 単独列（ループあり）
            ret_cur_column_info = copy.deepcopy(previous_column_info)
            ret_cur_column_info["sub_columns_info"]["sub_columns"].append( \
                create_column_info_single_repeats(basic_obj, previous_column_info))
            ret_line_status = 1

    return ret_cur_column_info, ret_final_previous_column_info, ret_line_status



# 単純に、rowをオブジェクトに変換する
def parse_one_line_simple(row):
    # B列: 項番
    seq = row[convert_to_index("B")]
    # C列: 副項番
    sub_seq = row[convert_to_index("C")]
    # D列: キー
    is_pk = row[convert_to_index("D")]
    # E列: 項目名
    column_name_jp = row[convert_to_index("E")]
    # W列: 項目名（英語）
    column_name_en = row[convert_to_index("W")]
    # F列: 位置
    start_pos = row[convert_to_index("F")]
    # G列: 繰り返し数
    repeats = row[convert_to_index("G")]
    # H列: バイト数
    bytes = row[convert_to_index("H")]
    # I列: 合計バイト数
    bytes_total = row[convert_to_index("I")]
    # J列: 初期値（パディング文字）
    padding_character = row[convert_to_index("J")]
    # K列: コメント
    comment = row[convert_to_index("K")]
    # X列: データ型
    db_column_type = row[convert_to_index("X")]
    # Y列: サイズ1
    db_column_size1 = row[convert_to_index("Y")]
    # Z列: サイズ2
    db_column_size2 = row[convert_to_index("Z")]
    # AA列: NotNull
    db_column_notnull = row[convert_to_index("AA")]
    # AB列: 繰返対応方法
    repat_item_handling = row[convert_to_index("AB")]
    # AC列: 横持ちsuffix（横持ちの場合のsuffix指定）
    repeat_suffix_rule = row[convert_to_index("AC")]

    return {
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
        "db_column_type": db_column_type,
        "db_column_size1": db_column_size1,
        "db_column_size2": db_column_size2,
        "db_column_notnull": db_column_notnull,
        "repat_item_handling": repat_item_handling,
        "repeat_suffix_rule": repeat_suffix_rule,
    }



# 使用すべき行か、またはスキップするかを確認する
# 引数:
#       simple_obj: 単純なオブジェクト
# 戻り値:
#       True: 使用すべき行
#       False: スキップする行
def     is_valid_line(simple_obj):
    # seqもsub_seqも空の場合は、スキップ
    seq = get_value(simple_obj["seq"], simple_obj["seq"], "")
    sub_seq = get_value(simple_obj["sub_seq"], simple_obj["sub_seq"], "")
    if (seq == "") and (sub_seq == ""):
        return False

    # 項目名が空の場合は、スキップ
    column_name_jp = get_value(simple_obj["column_name_jp"], simple_obj["column_name_jp"], "")
    if column_name_jp == "":
        return False
    
    # 型の定義がない、かつ、項目名が"<"で始まらない場合は、スキップ
    # （DBに取り込まない、かつ、繰り返しの指示行でもないという意味）
    db_column_type = get_value(simple_obj["db_column_type"], simple_obj["db_column_type"], "")
    if (db_column_type == "") and \
        (column_name_jp[0] != "<"):
        return False

    return True



# 使用すべき行である前提で、入力チェック
# 引数:
#       simple_obj: 単純なオブジェクト
# 戻り値:
#       True: 入力チェックOK
#       False: 入力チェックNG（assertでエラーを出し止まるので、Falseは返らないはず）
def check_input(simple_obj):
    # 単独項目
    #assert simple_obj["seq"] is not None, "項番が取得できません"
    #assert simple_obj["sub_seq"] is not None, "副項番が取得できません"
    #assert simple_obj["is_pk"] is not None, "キーが取得できません"
    assert simple_obj["column_name_jp"] is not None, "項目名が取得できません"
    assert simple_obj["column_name_en"] is not None, "項目名（英語）が取得できません"
    #assert simple_obj["column_name_en"] != "該当なし", "項目名（英語）が「該当なし」です"
    assert simple_obj["start_pos"] is not None, "開始位置が取得できません"
    #assert simple_obj["repeats"] is not None, "繰り返し数が取得できません"
    assert simple_obj["bytes"] is not None, "バイト数が取得できません"
    #assert simple_obj["bytes_total"] is not None, "合計バイト数が取得できません"
    #assert simple_obj["padding_character"] is not None, "初期値（パディング文字）が取得できません"
    #assert simple_obj["comment"] is not None, "コメントが取得できません"
    #assert simple_obj["db_column_type"] is not None, "データ型が取得できません"
    assert simple_obj["db_column_size1"] is not None, "サイズ1が取得できません"
    #assert simple_obj["db_column_size2"] is not None, "サイズ2が取得できません"
    #assert simple_obj["db_column_notnull"] is not None, "NotNullが取得できません"
    #assert simple_obj["repat_item_handling"] is not None, "繰返対応方法が取得できません"
    #assert simple_obj["repeat_suffix_rule"] is not None, "横持ちsuffixが取得できません"

    # 複合項目
    assert (simple_obj["seq"] is not None) or (simple_obj["sub_seq"] is not None), "項番または副項番が取得できません"
    repeats = get_value(simple_obj["repeats"], simple_obj["repeats"], 0)
    if repeats > 0:
        assert simple_obj["bytes_total"] == simple_obj["bytes"] * simple_obj["repeats"], "合計バイト数の計算が一致しません"
        assert simple_obj["repat_item_handling"] is not None, "繰返対応方法が取得できません"
        # seq、sub_seqの両方があるときは、データ型が必要
        if (simple_obj["seq"] is not None) and (simple_obj["sub_seq"] is not None):
            assert simple_obj["db_column_type"] is not None, "データ型が取得できません"
    else:
        assert simple_obj["column_name_en"] != "該当なし", "項目名（英語）が「該当なし」です"
        assert simple_obj["db_column_type"] is not None, "データ型が取得できません"

    return True



# 型の変換
# 引数:
#       simple_obj: 単純なオブジェクト
# 戻り値:
#       型の変換後のオブジェクト
def convert_to_basic_obj(simple_obj):
    # 項番
    seq = get_value(simple_obj["seq"], simple_obj["seq"], 0)
    seq = int(seq)
    # 副項番
    sub_seq = get_value(simple_obj["sub_seq"], simple_obj["sub_seq"], "")
    # キー
    is_pk = get_value(simple_obj["is_pk"], True, False)
    # 項目名
    column_name_jp = get_value(simple_obj["column_name_jp"], simple_obj["column_name_jp"], "")
    column_name_jp = re.sub(r'^　+', '', column_name_jp)
    # 項目名（英語）
    column_name_en = get_value(simple_obj["column_name_en"], simple_obj["column_name_en"], "")
    # 開始位置
    start_pos = get_value(simple_obj["start_pos"], simple_obj["start_pos"], 0)
    start_pos = re.sub(r'[\(\)\s]', '', str(start_pos))
    start_pos = int(start_pos)
    # 繰り返し数
    repeats = get_value(simple_obj["repeats"], simple_obj["repeats"], 0)
    # バイト数
    bytes = get_value(simple_obj["bytes"], simple_obj["bytes"], 0)
    bytes = int(bytes)
    # 合計バイト数
    bytes_total = get_value(simple_obj["bytes_total"], simple_obj["bytes_total"], 0)
    bytes_total = int(bytes_total)
    # 初期値（パディング文字）
    padding_character = get_value(simple_obj["padding_character"], simple_obj["padding_character"], "")
    padding_character = str(padding_character)
    # コメント
    comment = get_value(simple_obj["comment"], simple_obj["comment"], "")
    # データ型
    db_column_type = get_value(simple_obj["db_column_type"], simple_obj["db_column_type"], "")
    # サイズ1
    db_column_size1 = get_value(simple_obj["db_column_size1"], simple_obj["db_column_size1"], 0)
    db_column_size1 = int(db_column_size1)
    # サイズ2
    db_column_size2 = get_value(simple_obj["db_column_size2"], simple_obj["db_column_size2"], 0)
    db_column_size2 = int(db_column_size2)
    db_column_length = db_column_size1 if db_column_size2 == 0 else [db_column_size1, db_column_size2]
    # NotNull
    db_column_notnull = get_value(simple_obj["db_column_notnull"], True, False)
    # 繰返対応方法
    repat_item_handling = get_value(simple_obj["repat_item_handling"], simple_obj["repat_item_handling"], "")
    # 横持ちsuffix
    repeat_suffix_rule = get_value(simple_obj["repeat_suffix_rule"], simple_obj["repeat_suffix_rule"], "")
    if repeat_suffix_rule != "":
        repeat_suffix_rule = repeat_suffix_rule.split(",")
    else:
        repeat_suffix_rule = []

    return {
        "seq": seq,     # int
        "sub_seq": sub_seq,  # str
        "is_pk": is_pk,  # bool
        "column_name_jp": column_name_jp,  # str
        "column_name_en": column_name_en,  # str
        "start_pos": start_pos,  # int
        "repeats": repeats,  # int
        "bytes": bytes,  # int
        "bytes_total": bytes_total,  # int
        "padding_character": padding_character,  # str
        "comment": comment,  # str
        "db_column_type": db_column_type,  # str
        "db_column_length": db_column_length,  # int or list
        "db_column_notnull": db_column_notnull,  # bool
        "repat_item_handling": repat_item_handling,  # str
        "repeat_suffix_rule": repeat_suffix_rule,  # list
    }



# 値の取得
# 「空」とは、None、numpy.NaN、""のいずれか
# 引数:
#       value: 値
#       if_not_empty: 値が空でない場合の値
#       if_empty: 値が空の場合の値
# 戻り値:
#       値
def get_value(value, if_not_empty, if_empty):
    if value is None:
        return if_empty
    elif isinstance(value, float) and np.isnan(value):
        return if_empty
    elif isinstance(value, str) and value == "":
        return if_empty
    else:
        return if_not_empty



# 単独列（ループなし）の場合のオブジェクトを作成する
def create_column_info_single_no_repeats(basic_obj, cur_column_info = None):
    retObj = {}

    if basic_obj["seq"] != 0:
        retObj["seq"] = basic_obj["seq"]
    else:
        if cur_column_info is not None:
            retObj["seq"] = cur_column_info["seq"]
        else:
            retObj["seq"] = 0
    if basic_obj["sub_seq"] != "":
        retObj["sub_seq"] = basic_obj["sub_seq"]
    retObj["is_pk"] = basic_obj["is_pk"]
    retObj["column_name_jp"] = basic_obj["column_name_jp"]
    retObj["column_name_en"] = basic_obj["column_name_en"]
    retObj["start_pos"] = basic_obj["start_pos"]
    retObj["bytes"] = basic_obj["bytes"]
    retObj["bytes_total"] = basic_obj["bytes"]
    retObj["padding_character"] = basic_obj["padding_character"]
    if basic_obj["comment"] != "":
        retObj["comment"] = basic_obj["comment"]
    retObj["db_column_type"] = basic_obj["db_column_type"]
    retObj["db_column_length"] = basic_obj["db_column_length"]
    retObj["db_column_notnull"] = basic_obj["db_column_notnull"]

    return retObj



# 単独列（ループあり）の場合のオブジェクトを作成する
def create_column_info_single_repeats(basic_obj, cur_column_info = None):

    # 1つ目のサブカラム
    one_sub_column = {}
    if cur_column_info is None:
        # トップレベルの場合
        one_sub_column["seq"] = basic_obj["seq"]
        one_sub_column["sub_seq"] = "a"
    else:
        # ループ内の場合
        one_sub_column["seq"] = cur_column_info["seq"]
        one_sub_column["sub_seq"] = f"{basic_obj["sub_seq"]},a"
    one_sub_column["is_pk"] = basic_obj["is_pk"]
    one_sub_column["column_name_jp"] = basic_obj["column_name_jp"]
    one_sub_column["column_name_en"] = basic_obj["column_name_en"]
    one_sub_column["start_pos"] = 1
    one_sub_column["bytes"] = basic_obj["bytes"]
    one_sub_column["bytes_total"] = basic_obj["bytes"]
    one_sub_column["padding_character"] = basic_obj["padding_character"]
    one_sub_column["comment"] = basic_obj["comment"]
    one_sub_column["db_column_type"] = basic_obj["db_column_type"]
    one_sub_column["db_column_length"] = basic_obj["db_column_length"]
    one_sub_column["db_column_notnull"] = basic_obj["db_column_notnull"]

    # サブカラムの情報
    sub_columns_info = {}
    sub_columns_info["repeats"] = basic_obj["repeats"]
    sub_columns_info["repat_item_handling"] = basic_obj["repat_item_handling"]
    if basic_obj["repeat_suffix_rule"] != []:
        sub_columns_info["repeat_suffix_rule"] = basic_obj["repeat_suffix_rule"]
    sub_columns_info["sub_columns"] = []
    sub_columns_info["sub_columns"] = [one_sub_column]

    # 全体の情報
    retObj = {}
    if cur_column_info is None:
        # トップレベルの場合
        retObj["seq"] = basic_obj["seq"]
        assert basic_obj["sub_seq"] == "", "トップレベルの場合、sub_seqは空のはずですが入っています"
        if basic_obj["sub_seq"] != "":
            retObj["sub_seq"] = basic_obj["sub_seq"]    # たぶんない
    else:
        # ループ内の場合
        retObj["seq"] = cur_column_info["seq"]
        assert basic_obj["sub_seq"] != "", "ループ内の場合、sub_seqは空でないはずですが空です"
        if basic_obj["sub_seq"] != "":
            retObj["sub_seq"] = basic_obj["sub_seq"]    # たぶん必ずある
    retObj["is_pk"] = basic_obj["is_pk"]
    retObj["column_name_jp"] = basic_obj["column_name_jp"]
    retObj["column_name_en"] = basic_obj["column_name_en"]
    retObj["start_pos"] = basic_obj["start_pos"]
    retObj["bytes"] = basic_obj["bytes"]
    retObj["bytes_total"] = basic_obj["bytes_total"]
    retObj["padding_character"] = basic_obj["padding_character"]
    if basic_obj["comment"] != "":
        retObj["comment"] = basic_obj["comment"]
    retObj["sub_columns_info"] = sub_columns_info
    
    return retObj



# 複数ループ開始の場合のオブジェクトを作成する
def create_column_info_repeat_start(basic_obj):
    # サブカラムの情報
    sub_columns_info = {}
    sub_columns_info["repeats"] = basic_obj["repeats"]
    sub_columns_info["repat_item_handling"] = basic_obj["repat_item_handling"]
    if basic_obj["repeat_suffix_rule"] != []:
        sub_columns_info["repeat_suffix_rule"] = basic_obj["repeat_suffix_rule"]
    sub_columns_info["sub_columns"] = []    # この時点では空

    # 全体の情報
    retObj = {}
    retObj["seq"] = basic_obj["seq"]
    retObj["is_pk"] = basic_obj["is_pk"]
    retObj["column_name_jp"] = basic_obj["column_name_jp"]
    retObj["column_name_en"] = basic_obj["column_name_en"]
    retObj["start_pos"] = basic_obj["start_pos"]
    retObj["bytes"] = basic_obj["bytes"]
    retObj["bytes_total"] = basic_obj["bytes_total"]
    retObj["padding_character"] = basic_obj["padding_character"]
    if basic_obj["comment"] != "":
        retObj["comment"] = basic_obj["comment"]
    retObj["sub_columns_info"] = sub_columns_info

    return retObj
