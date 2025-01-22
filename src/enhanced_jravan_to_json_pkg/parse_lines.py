"""
与えられたDataFrameを、オブジェクトの配列に変換する
"""

import pandas as pd

from .parse_one_line import parse_one_line


def parse_lines(df):
    # 戻り値のオブジェクトを作成する
    retObj = []

    # １行ずつ、オブジェクトに変換する
    previous_column_info = None
    df_row_index = -1
    for index, row in df.iterrows():
        df_row_index += 1
        # ヘッダーは無条件にスキップ
        if df_row_index < 2:
            continue

        # １行のデータをオブジェクトに変換する
        column_info, final_previous_column_info, line_status = \
            parse_one_line(row, previous_column_info)
        
        # 引数として渡した、前回の列データの処理
        if ((line_status == 0) or (line_status == 1)) and \
            (final_previous_column_info is not None):
            # もし、前回の列データが確定していたら、それを追加する
            retObj.append(final_previous_column_info)

        # 今回のrowのデータの処理
        if line_status == 0:
            # 新しい行として、１列の情報を読み込んだ
            retObj.append(column_info)
            previous_column_info = None

        elif line_status == 1:
            # 次に続く可能性があるため、次回呼び出し時は今回の戻り値を引数に与える必要あり
            previous_column_info = column_info

        elif line_status == -1:
            # 空行などで、データとしては不要
            # previous_column_infoは更新しない（空だったら空、あればそのまま）
            pass

        else:
            # エラー
            raise Exception("parse_one_lineでエラーが発生しました")
    
    # 最後の行の処理
    if previous_column_info is not None:
        retObj.append(previous_column_info)


    return retObj


