import gradio as gr
import json
import os
import ui_layout

CONFIG_FILE = "config.json"

def load_config():
    default_config = {
        "comfy_url": "http://127.0.0.1:8188",
        "comfy_input_dir": "E:/GenAIs/StabilityMatrix-win-x64/Data/Packages/ComfyUI/input",
        "upscaler_workflow_file": "upscaler-tensorrt.json",
        "launch_bat": "E:/GenAIs/StabilityMatrix-win-x64/comfyui.bat",
        "server_port": 7685,
        # アップローダーリンクをリスト形式で追加
        "uploader_links": [
            {"name": "Catbox", "url": "https://catbox.moe/"},
            {"name": "ただのうｐろだ", "url": "https://tadaup.jp/"}
        ]
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # デフォルト値をマージして不足キーを補完
                for k, v in default_config.items():
                    if k not in config:
                        config[k] = v
                return config
        except Exception:
            pass
    return default_config

def save_config(config_dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=4, ensure_ascii=False)
    return "✅ 設定を config.json に保存しました。ポート変更の反映にはアプリの再起動が必要です。"

if __name__ == "__main__":
    config = load_config()
    demo = ui_layout.create_ui(config, save_config, load_config)
    
    port = config.get("server_port", 7685)
    print(f"Starting server on port {port}...")
    # 引数に title と theme を追加します
demo.launch(
    server_name="0.0.0.0", 
    server_port=port,
    theme=gr.themes.Default(primary_hue="orange")
)