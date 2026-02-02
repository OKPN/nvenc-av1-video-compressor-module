import os
import math
import re

def get_file_size_str(file_path):
    """(既存関数) ファイルパスを受け取り、読みやすいサイズ文字列(MB/KB)を返す"""
    if not os.path.exists(file_path):
        return "0 KB"
    size_bytes = os.path.getsize(file_path)
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / 1024:.2f} KB"

def format_size_extended(size_bytes):
    """(新規追加) バイト単位のサイズを最適な単位(B〜TB)に変換して返す"""
    if size_bytes == 0: return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    # 範囲外のエラーを防ぐ
    i = min(i, len(size_name) - 1)
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def safe_filename(name, max_length=120):
    """(既存関数) ファイル名に使えない文字を置換し、長さを制限する"""
    # Windowsでファイル名に使えない文字をアンダースコアに置換
    name = re.sub(r'[\\/:*?"<>|]', '_', name).strip()
    return name[:max_length]