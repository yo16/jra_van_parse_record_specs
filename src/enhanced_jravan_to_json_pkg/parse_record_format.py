"""
１つのレコードフォーマットを、オブジェクトに変換する
"""

import pandas as pd

from .parse_header import parse_header
from .parse_lines import parse_lines


def parse_record_format(df):
    # ヘッダー情報をオブジェクトに変換する
    header_object = parse_header(df)

    # 行情報をオブジェクトの配列に変換する
    lines_object = parse_lines(df)

    # ヘッダーと行情報から、戻り値を設定する
    retObj = {
        "header": header_object,
        "columns": lines_object
    }

    return retObj

