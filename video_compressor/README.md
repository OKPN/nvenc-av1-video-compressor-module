# NVENC AV1 Video Compressor Module

他アプリへの組込み・連結およびリモート利用を前提として設計された、NVIDIA NVENC ハードウェアアクセラレーション対応の超高速 AV1 動画一括圧縮モジュール ＆ Web UI アプリです。

---

## 📌 重要な前提条件

- **対応 GPU**: **NVIDIA GeForce RTX 40シリーズ以降** (Ada Lovelace 世代以降: RTX 4060 / 4070 / 4080 / 4090 / RTX Laptop GPU 等) または **AV1 NVENC エンコードに対応した NVIDIA GPU**
- **動作環境**: Windows 10 / 11
- **Python**: Python 3.10 以上

---

## 📦 インストール ＆ 起動コマンド

```bash
# 1. リポジトリのクローン ＆ 移動
git clone https://github.com/OKPN/nvenc-av1-video-compressor-module.git
cd nvenc-av1-video-compressor-module

# 2. 自動起動バッチの実行
start_video_compressor.bat
```

## 💻 他アプリへの組み込み方法

ご自身の Gradio コードに `video_compressor` をインポートするだけで、1 行で動画圧縮タブを連結できます：

```python
import gradio as gr
import video_compressor

with gr.Blocks() as my_app:
    with gr.Tabs():
        with gr.Tab("🎬 動画圧縮"):
            # 1行でUIコンポーネントとエンコード処理を埋め込み可能
            video_compressor.create_video_compress_tab()

my_app.launch()
```

---

## 🗑️ アンインストール方法

不要になった場合は、**本フォルダ全体を削除するだけ**でアンインストールが完了します。
*(※ FFmpeg も削除したい場合は、気になるならアプリ内の「⚙️ 設定」タブから「🗑️ アンインストール (Winget)」を押して FFmpeg を削除してから、フォルダを削除してください)*
