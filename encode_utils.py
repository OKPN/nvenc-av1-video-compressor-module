import subprocess
import os
import tempfile
from pathlib import Path
from PIL import Image
import concurrent.futures
import gradio as gr
# 新しい format_size_extended をインポート
from file_utils import get_file_size_str, format_size_extended

# --- (既存の関数: encode_video, encode_image_jxl, optimize_image_standard はそのまま維持) ---
# --- 動画エンコード ---
def encode_video(input_file_path):
    if input_file_path is None: return None
    temp_dir = tempfile.gettempdir()
    stem_name = Path(input_file_path).stem
    output_path = os.path.join(temp_dir, f"{stem_name}_output.mp4")
    
    command = [
        "ffmpeg", "-y", "-i", input_file_path,
        "-c:v", "av1_nvenc", "-rc:v", "vbr", "-cq:v", "40", "-preset", "p4",
        "-c:a", "copy", output_path
    ]
    try:
        subprocess.run(command, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"動画エラー: {e}")
        return None

# --- 画像エンコード (JPEG XL - 単発/ffmpeg経由) ---
def encode_image_jxl(input_image_path, distance=1.0, effort=7):
    """
    distance: 0.0=無劣化, 1.0=標準, 2.0-4.0=高圧縮
    effort: 1-9 (圧縮にかける手間)
    """
    if input_image_path is None: return None, "", "", ""
    input_size = get_file_size_str(input_image_path)
    
    temp_dir = tempfile.gettempdir()
    stem_name = Path(input_image_path).stem
    output_path = os.path.join(temp_dir, f"{stem_name}.jxl")

    # ffmpegコマンドに effort を追加
    command = [
        "ffmpeg", "-y", "-i", input_image_path,
        "-c:v", "libjxl", 
        "-distance", str(distance),
        "-effort", str(effort),
        output_path
    ]
    try:
        subprocess.run(command, check=True)
        output_size = get_file_size_str(output_path)
        
        in_bytes = os.path.getsize(input_image_path)
        out_bytes = os.path.getsize(output_path)
        reduction = (1 - (out_bytes / in_bytes)) * 100 if in_bytes > 0 else 0
        
        return output_path, input_size, output_size, f"JXL変換成功 ({reduction:.1f}% 削減)"
    except subprocess.CalledProcessError as e:
        return None, "エラー", "エラー", f"失敗: {e}"

# --- 画像最適化 (互換モード) ---
def optimize_image_standard(input_image_path, quality, convert_to_jpeg):
    if input_image_path is None: return None, "", "", ""
    
    input_size = get_file_size_str(input_image_path)
    temp_dir = tempfile.gettempdir()
    original_path = Path(input_image_path)
    
    try:
        img = Image.open(input_image_path)
    except Exception as e:
        return None, "エラー", "エラー", f"画像が開けませんでした: {e}"

    is_jpeg_target = convert_to_jpeg or original_path.suffix.lower() in ['.jpg', '.jpeg']
    
    if is_jpeg_target:
        output_filename = f"{original_path.stem}_opt.jpg"
        output_path = os.path.join(temp_dir, output_filename)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=int(quality), optimize=True, progressive=True)
    else:
        output_filename = f"{original_path.stem}_opt.png"
        output_path = os.path.join(temp_dir, output_filename)
        img.save(output_path, "PNG", optimize=True)

    output_size = get_file_size_str(output_path)
    in_bytes = os.path.getsize(input_image_path)
    out_bytes = os.path.getsize(output_path)
    reduction = (1 - (out_bytes / in_bytes)) * 100 if in_bytes > 0 else 0
    
    return output_path, input_size, output_size, f"最適化完了 ({reduction:.1f}% 削減)"

# ==========================================
# --- 以下、新規追加: JXL一括変換ロジック ---
# ==========================================

def _convert_single_file_jxl_batch(input_path, output_path, distance, effort, strip_metadata, cjxl_path):
    """一括変換用の内部関数: 個別のファイルを変換"""
    try:
        input_size = input_path.stat().st_size
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # コマンドの構築
        cmd = [
            cjxl_path, str(input_path), str(output_path),
            "-d", str(distance),
            "-e", str(effort),
            "--quiet"
        ]

        # Distanceが指定されている場合、JPEGの自動ロスレス再構築をオフにする
        if distance > 0:
            cmd.append("--lossless_jpeg=0")
            
        # メタデータ削除フラグ
        if strip_metadata:
            cmd.append("--strip")
        
        # 実行
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            output_size = output_path.stat().st_size
            return True, input_size, output_size, f"成功: {input_path.name}"
        else:
            return False, 0, 0, f"失敗: {input_path.name}\n  エラー: {result.stderr}"
    except Exception as e:
        return False, 0, 0, f"例外エラー: {input_path.name}\n  詳細: {str(e)}"

def batch_encode_jxl_recursive(input_root_str, output_root_str, distance, effort, strip_metadata, progress=gr.Progress()):
    """JXL再帰的一括変換のメイン関数"""
    input_root = Path(input_root_str)
    output_root = Path(output_root_str)
    
    if not input_root_str or not input_root.exists():
        return "エラー: 入力フォルダが存在しません。", ""
    if not output_root_str:
         return "エラー: 出力フォルダーを指定してください。", ""

    # cjxl.exe のパス解決 (このスクリプトと同じディレクトリを探す)
    cjxl_exe = Path(__file__).parent / "cjxl.exe"
    cjxl_path = str(cjxl_exe) if cjxl_exe.exists() else "cjxl"

    # 変換対象の拡張子
    extensions = {".png", ".jpg", ".jpeg"}
    files_to_process = []

    # 再帰的にファイルを探索
    progress(0, desc="ファイル探索中...")
    for path in input_root.rglob("*"):
        if path.suffix.lower() in extensions:
            # 入力ルートからの相対パスを維持して出力パスを作成
            relative_path = path.relative_to(input_root)
            output_path = output_root / relative_path.with_suffix(".jxl")
            files_to_process.append((path, output_path))

    total_files = len(files_to_process)
    if total_files == 0:
        return "対象画像が見つかりませんでした。", "### 統計\n対象ファイルなし"

    total_input_size = 0
    total_output_size = 0
    success_count = 0
    logs = []
    
    # 並列処理の実行
    # CPUコア数に応じて自動でワーカー数が調整される
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(_convert_single_file_jxl_batch, inp, outp, distance, effort, strip_metadata, cjxl_path): inp 
            for inp, outp in files_to_process
        }
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            success, in_size, out_size, log_msg = future.result()
            logs.append(log_msg)
            if success:
                total_input_size += in_size
                total_output_size += out_size
                success_count += 1
            # 進捗バーの更新
            progress((i + 1) / total_files, desc=f"変換中: {i+1}/{total_files}")

    # 統計レポートの作成
    reduction = total_input_size - total_output_size
    reduction_percent = (reduction / total_input_size * 100) if total_input_size > 0 else 0
    
    summary_md = f"""
### 📊 変換統計レポート
| 項目 | 内容 |
| :--- | :--- |
| **処理成功数** | {success_count} / {total_files} 件 |
| **変換前合計** | {format_size_extended(total_input_size)} |
| **変換後合計** | {format_size_extended(total_output_size)} |
| **削減容量** | **{format_size_extended(reduction)}** |
| **容量削減率** | **{reduction_percent:.2f} %** |
    """
    
    final_log = "\n".join(logs)
    if not final_log: final_log = "処理完了。ログはありません。"

    return final_log, summary_md