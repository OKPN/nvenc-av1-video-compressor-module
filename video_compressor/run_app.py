"""
Video Compressor Package Standalone Launcher
"""
import json
import os
import sys
import time
import threading
import webbrowser
from pathlib import Path

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 親ディレクトリを sys.path に追加してパッケージとして読み込み可能にする
package_dir = Path(__file__).resolve().parent
parent_dir = package_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import video_compressor

CONFIG_FILE = parent_dir / "config.json"

def load_config():
    default_config = {
        "server_port": 7861,
        "auto_open_browser": True
    }
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
    start_port = config.get("server_port", 7861)
    auto_open = config.get("auto_open_browser", True)

    app = video_compressor.create_video_compressor_app(
        title="NVENC AV1 Video Compressor Module"
    )
    
    current_port = start_port
    max_attempts = 50

    for attempt in range(max_attempts):
        try:
            print(f"[NVENC AV1 Video Compressor Module] Trying port {current_port}...")
            
            if auto_open:
                target_url = f"http://localhost:{current_port}"
                def _open_browser_thread():
                    time.sleep(1.2)
                    print(f"[NVENC AV1 Video Compressor Module] Automatically opening browser: {target_url}")
                    webbrowser.open(target_url)
                threading.Thread(target=_open_browser_thread, daemon=True).start()

            app.launch(
                server_name="0.0.0.0",
                server_port=current_port
            )
            break
        except OSError:
            print(f"[NVENC AV1 Video Compressor Module] Port {current_port} is in use. Retrying with port {current_port + 1}...")
            current_port += 1

if __name__ == "__main__":
    main()
