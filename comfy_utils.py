import json
import requests
import time
import uuid
import io
from pathlib import Path
from PIL import Image

def load_workflow(workflow_path):
    """ワークフローJSONを読み込む"""
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def find_node_by_class(prompt, class_name):
    """指定したクラス名のノードIDを探す"""
    for node_id, node in prompt.items():
        if node.get("class_type") == class_name:
            return node_id
    return None

def find_textencode_node(prompt):
    """KSamplerに繋がっているPositiveプロンプトのノードを探す"""
    sampler_id = find_node_by_class(prompt, "KSampler")
    if not sampler_id:
        return None

    try:
        positive_input = prompt[sampler_id]["inputs"]["positive"]
        target_node_id = positive_input[0]
        if target_node_id in prompt:
            return target_node_id
    except (KeyError, IndexError, TypeError):
        pass
    return None

def find_angle_lora_node(prompt):
    """'多角度'を含むLoRAノードを探す"""
    for node_id, node in prompt.items():
        if "LoraLoader" in node.get("class_type", ""):
            lora_name = node["inputs"].get("lora_name", "")
            if "多角度" in lora_name: 
                return node_id
    return None

def save_input_image(img: Image.Image, input_dir_path):
    """画像をComfyUIのinputフォルダに保存する"""
    input_dir = Path(input_dir_path)
    if not input_dir.exists():
        raise RuntimeError(f"ComfyUI input directory not found: {input_dir}")
    
    name = f"gr_{uuid.uuid4().hex}.png"
    img.save(input_dir / name)
    return name

def run_comfy_api(prompt, comfy_url):
    """ComfyUIにジョブを送信し、完了を待って画像を取得する"""
    # 1. ジョブ送信
    try:
        r = requests.post(f"{comfy_url}/prompt", json={"prompt": prompt}, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"ComfyUI connection failed: {e}")

    prompt_id = r.json()["prompt_id"]

    # 2. 完了待機 (ポーリング)
    while True:
        try:
            h = requests.get(f"{comfy_url}/history/{prompt_id}", timeout=5).json()
            if prompt_id in h:
                break
            time.sleep(0.5)
        except requests.RequestException:
            time.sleep(1) # エラー時は少し待って再試行

    # 3. 出力画像の特定
    outputs = h[prompt_id]["outputs"]
    target_img_info = None
    for node in outputs.values():
        if "images" in node:
            target_img_info = node["images"][0]
            break
    
    if not target_img_info:
        raise RuntimeError("No output image found in history")

    # 4. 画像データの取得
    params = {
        "filename": target_img_info["filename"],
        "type": target_img_info.get("type", "output"),
        "subfolder": target_img_info.get("subfolder", "")
    }
    
    img_res = requests.get(f"{comfy_url}/view", params=params, timeout=20)
    img_res.raise_for_status()
    
    return Image.open(io.BytesIO(img_res.content)).convert("RGB")

def generate_image(image: Image.Image, text: str, bypass_lora: bool, config: dict):
    """メイン生成処理"""
    workflow_path = config.get("workflow_file")
    input_dir = config.get("comfy_input_dir")
    comfy_url = config.get("comfy_url")

    # ワークフロー読み込み
    prompt = load_workflow(workflow_path)
    if not prompt:
        return None, f"Error: Workflow file '{workflow_path}' not found."

    # ノード探索
    node_image = find_node_by_class(prompt, "LoadImage")
    node_text = find_textencode_node(prompt)
    node_lora = find_angle_lora_node(prompt)

    if not node_image: return None, "Error: LoadImage node not found."
    if not node_text: return None, "Error: TextEncode node not found."

    # 画像保存 & パス設定
    try:
        fname = save_input_image(image, input_dir)
    except Exception as e:
        return None, str(e)

    prompt[node_image]["inputs"]["image"] = fname
    prompt[node_text]["inputs"]["prompt"] = text

    # LoRA Bypass設定
    if node_lora:
        strength = 0 if bypass_lora else 1
        inputs = prompt[node_lora]["inputs"]
        if "strength_model" in inputs: inputs["strength_model"] = strength
        if "strength" in inputs: inputs["strength"] = strength
        if "strength_clip" in inputs: inputs["strength_clip"] = strength

    # 実行
    try:
        out_image = run_comfy_api(prompt, comfy_url)
        return out_image, "Success"
    except Exception as e:
        return None, f"Generation Error: {e}"
    
def find_node_by_title(prompt, title):
    """
    ノードの _meta データの title 文字列からノードIDを探す
    """
    for node_id, node in prompt.items():
        if "_meta" in node and node["_meta"].get("title") == title:
            return node_id
    return None

def generate_image_qwen(image: Image.Image, az, el, dist, seed, steps, cfg, config: dict):
    workflow_path = config.get("workflow_file")
    input_dir = config.get("comfy_input_dir")
    comfy_url = config.get("comfy_url")

    prompt = load_workflow(workflow_path)
    if not prompt: return None, "Workflow file not found."

    # --- タイトル名でノードを特定 ---
    # JSONのタイトル名と完全に一致させる必要があります
    node_image  = find_node_by_title(prompt, "画像を読み込む")
    node_camera = find_node_by_title(prompt, "Qwen Multiangle Camera")
    node_sampler = find_node_by_title(prompt, "Kサンプラー")

    # 値の流し込み
    if node_image:
        fname = save_input_image(image, input_dir)
        prompt[node_image]["inputs"]["image"] = fname

    if node_camera:
        prompt[node_camera]["inputs"]["horizontal_angle"] = az
        prompt[node_camera]["inputs"]["vertical_angle"] = el
        prompt[node_camera]["inputs"]["zoom"] = dist

    if node_sampler:
        prompt[node_sampler]["inputs"]["seed"] = seed
        prompt[node_sampler]["inputs"]["steps"] = steps
        prompt[node_sampler]["inputs"]["cfg"] = cfg

    # 実行
    try:
        out_image = run_comfy_api(prompt, comfy_url)
        return out_image, "Success"
    except Exception as e:
        return None, f"Error: {e}"