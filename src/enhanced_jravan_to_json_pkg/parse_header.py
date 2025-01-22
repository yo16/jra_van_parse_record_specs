"""
与えられたDataFrameの、ヘッダー情報をオブジェクトに変換する
"""

import pandas as pd

from .utils import convert_to_index, convert_to_integer


# ヘッダー情報をオブジェクトに変換する
def parse_header(df):
    # 全体を単純に読み込む
    # AB列: レコード種別ID(type_id)
    record_type_id = df.iloc[0][convert_to_index("AB")]
    # X列: フォーマット番号(format_number)
    format_number = df.iloc[0][convert_to_index("X")]
    # Y列: フォーマット名・日本語(format_name_jp)
    format_name_jp = df.iloc[0][convert_to_index("Y")]
    # Z列: フォーマット名・英語(format_name_en)
    format_name_en = df.iloc[0][convert_to_index("Z")]
    # AA列: フォーマットのバイト数(total_bytes)
    total_bytes = df.iloc[0][convert_to_index("AA")]

    # 入力チェック
    assert record_type_id is not None, "レコード種別IDが取得できていません"
    assert format_number is not None, "フォーマット番号が取得できていません"
    assert format_name_jp is not None, "フォーマット名・日本語が取得できていません"
    assert format_name_en is not None, "フォーマット名・英語が取得できていません"
    assert total_bytes is not None, "フォーマットのバイト数が取得できていません"    

    # 必要に応じて型などを変換する
    format_number = convert_to_integer(format_number)
    total_bytes = int(total_bytes)

    # 戻り値のオブジェクトを作成する
    retObj = {
        "record_type_id": record_type_id,
        "format_number": format_number,
        "format_name_jp": format_name_jp,
        "format_name_en": format_name_en,
        "total_bytes": total_bytes
    }

    return retObj


