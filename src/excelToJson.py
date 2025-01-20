"""
JRA-VANのデータ仕様書（Excelファイル）をJSONに変換する
日本語から英語への翻訳は、data/translation.jsonに保存されている
"""

import pandas as pd

def excel_to_json(file_path):
    df = pd.read_excel(file_path)
    return df.to_json(orient='records')

