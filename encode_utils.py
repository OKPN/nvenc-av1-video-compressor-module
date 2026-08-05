import subprocess
import os
import tempfile
from pathlib import Path
from PIL import Image
import concurrent.futures
import gradio as gr
from file_utils import get_file_size_str, format_size_extended, safe_filename

# --- 動画エンコード (video_compressor パッケージに処理を委譲) ---
def encode_video(input_file_path):
    import video_compressor
    out_path, _ = video_compressor.compress_video(input_file_path)
    return out_path

# --- 画像エンコード (WebP) ---
def encode_image_webp(input_image_path, quality=85, lossless=False, strip_metadata=False, custom_filename=None):
    if input_image_path is None: return None, "", "", ""
    
    input_size = get_file_size_str(input_image_path)
    temp_dir = tempfile.gettempdir()
    original_path = Path(input_image_path)
    
    stem_name = safe_filename(custom_filename) if custom_filename and custom_filename.strip() else original_path.stem
    output_filename = f"{stem_name}.webp"
    output_path = os.path.join(temp_dir, output_filename)
    
    try:
        with Image.open(input_image_path) as img:
            # 透過 (Alpha) を保持するために必要に応じて RGBA に変換
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            save_args = {
                "format": "webp",
                "quality": int(quality),
                "lossless": lossless,
                "method": 6  # 最高圧縮効率 (処理時間は少しかかりますがファイルサイズを最小化)
            }

            # メタデータを残す場合
            if not strip_metadata and "exif" in img.info:
                save_args["exif"] = img.info["exif"]

            img.save(output_path, **save_args)

            # 統計計算
            output_size = get_file_size_str(output_path)
            in_bytes = os.path.getsize(input_image_path)
            out_bytes = os.path.getsize(output_path)
            reduction = (1 - (out_bytes / in_bytes)) * 100 if in_bytes > 0 else 0
            
            return output_path, input_size, output_size, f"WebP変換成功 ({reduction:.1f}% 削減)"

    except Exception as e:
        print(f"WebP encode error: {e}")
        return None, "エラー", "エラー", f"失敗: {str(e)}"

# --- 画像エンコード (JPEG XL - 単発/ffmpeg経由) ---
def encode_image_jxl(input_image_path, distance=1.0, effort=7, strip_metadata=False, custom_filename=None):
    """
    引数に strip_metadata と custom_filename を追加
    """
    if input_image_path is None: return None, "", "", ""
    input_size = get_file_size_str(input_image_path)
    
    temp_dir = tempfile.gettempdir()
    original_path = Path(input_image_path)
    
    stem_name = safe_filename(custom_filename) if custom_filename and custom_filename.strip() else original_path.stem
    output_path = os.path.join(temp_dir, f"{stem_name}.jxl")

    # ffmpegコマンドの構築
    command = [
        "ffmpeg", "-y", "-i", input_image_path,
        "-c:v", "libjxl", 
        "-distance", str(distance),
        "-effort", str(effort),
    ]

    # メタデータ削除設定 (-map_metadata -1 で全削除)
    if strip_metadata:
        command.extend(["-map_metadata", "-1"])
    
    command.append(output_path)

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
def optimize_image_standard(input_image_path, quality, convert_to_jpeg, strip_metadata=False, custom_filename=None):
    """
    引数に strip_metadata と custom_filename を追加し、ロジックを整理
    """
    if input_image_path is None: return None, "", "", ""
    
    input_size = get_file_size_str(input_image_path)
    temp_dir = tempfile.gettempdir()
    original_path = Path(input_image_path)
    
    stem_name = safe_filename(custom_filename) if custom_filename and custom_filename.strip() else original_path.stem
    
    try:
        with Image.open(input_image_path) as img:
            # JPEG変換設定の判定
            is_jpeg_target = convert_to_jpeg or original_path.suffix.lower() in ['.jpg', '.jpeg']
            
            if is_jpeg_target:
                output_filename = f"{stem_name}_opt.jpg"
                output_path = os.path.join(temp_dir, output_filename)
                # RGBAやPモード（透過あり）をRGBに変換しないとJPEGで保存できない
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                
                save_args = {"quality": int(quality), "optimize": True, "progressive": True}
            else:
                output_filename = f"{stem_name}_opt.png"
                output_path = os.path.join(temp_dir, output_filename)
                save_args = {"optimize": True}

            # メタデータを保持する場合のみ EXIF を渡す
            if not strip_metadata:
                if "exif" in img.info:
                    save_args["exif"] = img.info["exif"]

            img.save(output_path, **save_args)

            # 統計計算
            output_size = get_file_size_str(output_path)
            in_bytes = os.path.getsize(input_image_path)
            out_bytes = os.path.getsize(output_path)
            reduction = (1 - (out_bytes / in_bytes)) * 100 if in_bytes > 0 else 0
            
            return output_path, input_size, output_size, f"最適化完了 ({reduction:.1f}% 削減)"

    except Exception as e:
        print(f"Optimization error: {e}")
        return None, "エラー", "エラー", f"失敗: {str(e)}"

# --- JXL一括変換ロジック ---
def _convert_single_file_jxl_batch(input_path, output_path, distance, effort, strip_metadata, cjxl_path):
    """一括変換用の内部関数"""
    try:
        input_size = input_path.stat().st_size
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            cjxl_path, str(input_path), str(output_path),
            "-d", str(distance),
            "-e", str(effort),
            "--quiet"
        ]

        if distance > 0:
            cmd.append("--lossless_jpeg=0")
            
        if strip_metadata:
            cmd.append("--strip")
        
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

    cjxl_exe = Path(__file__).parent / "cjxl.exe"
    cjxl_path = str(cjxl_exe) if cjxl_exe.exists() else "cjxl"

    extensions = {".png", ".jpg", ".jpeg"}
    files_to_process = []

    progress(0, desc="ファイル探索中...")
    for path in input_root.rglob("*"):
        if path.suffix.lower() in extensions:
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
            progress((i + 1) / total_files, desc=f"変換中: {i+1}/{total_files}")

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
    return final_log, summary_md