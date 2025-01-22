"""
ユーティリティ関数
"""


# Google Spreadsheetの列名のアルファベットから、indexの整数へ変換する
# 列名は、A、B、C、...、Y、Z、AA、AB、... となっている
# ２文字以上になった場合の考慮が重要
def convert_to_index(column_name):
    column_name = column_name.upper()  # 小文字対応のため大文字に変換
    index = 0
    for char in column_name:
        # Aを1、Bを2、...とする計算
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1  # Aが0になるように調整



# 全角の数字を整数へ変換する
def convert_to_integer(value):
    return int(value.replace("０", "0").replace("１", "1").replace("２", "2").replace("３", "3").replace("４", "4").replace("５", "5").replace("６", "6").replace("７", "7").replace("８", "8").replace("９", "9"))

