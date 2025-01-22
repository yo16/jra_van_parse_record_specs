"""
JRA-VANのデータ仕様書を拡張した「拡張フォーマット.xlsx」を、JSONファイルに変換する
"""

from enhanced_jravan_to_json_pkg import enhanced_jravan_to_json

def main():
    enhanced_jravan_to_json(
        "./data/拡張フォーマット.xlsx",
        "フォーマット4901",
        "./data/recordFormat2.json"
    )


if __name__ == "__main__":
    main()
