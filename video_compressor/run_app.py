"""
Video Compressor Package Standalone Launcher
"""
import json
import os
import sys
from pathlib import Path

# 親ディレクトリを sys.path に追加してパッケージとして読み込み可能にする
package_dir = Path(__file__).resolve().parent
parent_dir = package_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import video_compressor

CONFIG_FILE = parent_dir / "config.json"

def load_config():
    default_config = {"server_port": 7685}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {**default_config, **cfg}
        except Exception:
            pass
    return default_config

def main():
    config = load_config()
    port = config.get("server_port", 7685)

    print(f"[NVENC AV1 Video Compressor Module] Starting module on port {port}...")
    
    app = video_compressor.create_video_compressor_app(
        title="NVENC AV1 Video Compressor Module"
    )
    
    try:
        app.launch(
            server_name="0.0.0.0",
            server_port=port
        )
    except OSError:
        print(f"[Video Compressor] Port {port} is occupied. Retrying with automatic free port...")
        app.launch(
            server_name="0.0.0.0"
        )

if __name__ == "__main__":
    main()
