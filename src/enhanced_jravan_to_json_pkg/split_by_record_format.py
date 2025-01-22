"""
与えられたDataFrameを、record_formatごとに分割する
"""

import pandas as pd
from .utils import convert_to_index

def split_by_record_format(df):
    # W列が"RECORD_DEFINITION"の行を探す
    record_definition_list = df[df.iloc[:, convert_to_index("W")] == "RECORD_DEFINITION"]

    # レコードフォーマットごとに分割したDataFrameのリストを格納する
    ret_df_list = []
    prev_start = 0
    for index, _ in record_definition_list.iterrows():
        current_index = int(index)

        if prev_start == 0:
            # 次のレコードフォーマットの開始位置を格納（初期値）
            prev_start = current_index
            continue

        # レコードフォーマットの開始位置から、次のレコードフォーマットの開始位置までのデータを格納
        ret_df_list.append(df.iloc[prev_start:current_index - 1])

        # 次のレコードフォーマットの開始位置を格納
        prev_start = current_index
    
    # 最後のレコードフォーマットのデータを格納
    ret_df_list.append(df.iloc[prev_start:df.shape[0]])

    return ret_df_list

