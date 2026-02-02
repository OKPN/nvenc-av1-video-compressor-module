import os
import tempfile
import uuid # 追加: ファイル名生成に必要
from pathlib import Path
import json
import comfy_utils # 既存の共通関数を利用
from PIL import Image

# 引数に original_path を追加して整合性を合わせる
def run_upscale(image: Image.Image, resize_to: str, model_name: str, config: dict, original_path=None):
    workflow_path = config.get("upscaler_workflow_file")
    input_dir = config.get("comfy_input_dir")
    comfy_url = config.get("comfy_url")

    # 1. ワークフロー読み込み
    prompt = comfy_utils.load_workflow(workflow_path)
    if not prompt:
        return None, "ワークフローファイルが見つかりません。"

    # 2. 入力画像の保存
    try:
        fname = comfy_utils.save_input_image(image, input_dir)
    except Exception as e:
        return None, f"画像の保存に失敗しました: {e}"

    # 3. JSON内のノードIDに値を流し込む
    if "5" in prompt:
        prompt["5"]["inputs"]["image"] = fname
    if "4" in prompt:
        prompt["4"]["inputs"]["model"] = model_name
    if "1" in prompt:
        prompt["1"]["inputs"]["resize_to"] = resize_to

    # 4. ComfyUI API実行
    try:
        out_image = comfy_utils.run_comfy_api(prompt, comfy_url)
        
        # --- 追加: ファイルとして一時保存 ---
        temp_dir = tempfile.gettempdir()
        
        # 入力ファイルの拡張子を取得（.png, .jpgなど）
        ext = Path(original_path).suffix if original_path else ".png"
        out_filename = os.path.join(temp_dir, f"upscaled_{uuid.uuid4().hex}{ext}")
        
        # 保存形式の判定
        save_format = "PNG" if ext.lower() == ".png" else "JPEG"
        if save_format == "JPEG":
            out_image = out_image.convert("RGB")
            out_image.save(out_filename, format=save_format, quality=95, subsampling=0)
        else:
            out_image.save(out_filename, format=save_format)
            
        return out_filename, "Success" # PILオブジェクトではなくパスを返す
    except Exception as e:
        return None, f"実行エラー: {e}"