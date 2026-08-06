"""
Video Compressor Package Standalone Launcher
"""
import json
import os
import sys
import time
import socket
import threading
import subprocess
import webbrowser
from pathlib import Path

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "0"

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

def check_port_available(host, port):
    """指定されたポートが実際にbind可能か厳密にチェックする (SO_REUSEADDR有効)"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False

def find_available_port(start_port, max_attempts=50):
    """初期ポートから順番に試行し、空いているポート番号を返す"""
    for port in range(start_port, start_port + max_attempts):
        if check_port_available("0.0.0.0", port):
            return port
    return start_port

def restart_app():
    """現在のPythonプロセスを終了し、新しいプロセスを立ち上げて再起動する"""
    python_exe = sys.executable
    script_path = os.path.abspath(sys.argv[0])
    
    print("[NVENC AV1 Video Compressor Module] Restarting application process...")
    subprocess.Popen([python_exe, script_path] + sys.argv[1:])
    time.sleep(0.5)
    os._exit(0)

def main():
    config = load_config()
    start_port = config.get("server_port", 7861)
    auto_open = config.get("auto_open_browser", True)

    selected_port = find_available_port(start_port)
    if selected_port != start_port:
        print(f"[NVENC AV1 Video Compressor Module] Port {start_port} is occupied. Automatically shifted to port {selected_port}.")
    else:
        print(f"[NVENC AV1 Video Compressor Module] Port {selected_port} is available.")

    app = video_compressor.create_video_compressor_app(
        title="NVENC AV1 Video Compressor Module",
        restart_func=restart_app
    )
    
    if auto_open:
        target_url = f"http://localhost:{selected_port}"
        def _open_browser_thread():
            time.sleep(1.5)
            print(f"[NVENC AV1 Video Compressor Module] Automatically opening browser: {target_url}")
            try:
                webbrowser.open(target_url)
            except Exception as e:
                print(f"[WARN] Failed to open browser automatically: {e}")
        threading.Thread(target=_open_browser_thread, daemon=True).start()

    try:
        app.launch(
            server_name="0.0.0.0",
            server_port=selected_port
        )
    except OSError:
        # 万一ソケットチェック通過後に他プロセスと競合した場合のフォールバック
        fallback_port = find_available_port(selected_port + 1)
        print(f"[NVENC AV1 Video Compressor Module] Retrying with fallback port {fallback_port}...")
        app.launch(
            server_name="0.0.0.0",
            server_port=fallback_port
        )

if __name__ == "__main__":
    main()
