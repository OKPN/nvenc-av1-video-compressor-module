# NVENC AV1 Video Compressor Module

他アプリへの組込み・連結を前提として設計された、NVIDIA NVENC ハードウェアアクセラレーション対応の超高速 AV1 動画一括圧縮モジュール ＆ Gradio UI です。

---

## 📌 重要な前提条件

- **対応 GPU**: **NVIDIA GeForce RTX 40シリーズ以降** (Ada Lovelace 世代以降: RTX 4060 / 4070 / 4080 / 4090 / RTX Laptop GPU 等) または **AV1 NVENC エンコードに対応した NVIDIA GPU**
  - ※ RTX 30シリーズ以前や AMD / Intel GPU、CPU のみの環境では `av1_nvenc` エンコーダが動作しません。
- **動作環境**: Windows 10 / 11
- **必須ツール**: FFmpeg (AV1 NVENC 対応版。※ アプリの設定画面からワンクリックで自動インストール可能)
- **Python**: Python 3.10 以上

---

## 🚀 特長

1. **他アプリへの簡単な組み込み (Module Design)**:
   - バックエンド処理 (`compress_video`) や Gradio UI コンポーネント (`create_video_compress_tab`) がモジュール化されており、他の Python アプリや Gradio UI へ 1 行で連結・組み込みが可能です。
2. **超高速一括圧縮**:
   - 複数動画ファイルおよびフォルダのドラッグ＆ドロップに対応。指定したフォルダ内の動画を再帰的に検索して全自動で一括変換します。
3. **ComfyUI などのメタデータを完全維持**:
   - 生成 AI (ComfyUI / AnimateDiff / VideoCombine 等) のプロンプトやワークフロー情報（JSON メタデータ）を脱落させずに動画内へそのまま継承します (`-map_metadata 0`)。
4. **細かな調整と設定の記憶**:
   - CQ値 (デフォルト: 32)、NVENC プリセット (デフォルト: p6)、出力ファイルの末尾サフィックス (デフォルト: `_compressed`) などを UI 上で変更でき、`config.json` に設定を記憶・自動復元します。
5. **FFmpeg 管理機能**:
   - システム環境チェック、ワンクリックでの自動インストール、最新版へのアップデートを UI 上から安全に行えます。

---

## 📦 インストール方法

### 1. リポジトリのクローン
```bash
git clone https://github.com/OKPN/nvenc-av1-video-compressor-module.git
cd nvenc-av1-video-compressor-module
```

### 2. 仮想環境の作成とライブラリのインストール
```bash
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

*(必要ライブラリ: `gradio`, `pillow`, `requests` 等)*

---

## 💻 使い方

### A. 動画圧縮モジュール単体で起動する場合

以下のいずれかのコマンドを実行すると、独立した軽量 Gradio Web UI が起動します：

```bash
python run_video_compressor.py
```
*(または `python video_compressor/run_app.py`)*

ブラウザで `http://localhost:7865` にアクセスしてご利用ください。

---

### B. 他の Gradio アプリにこのモジュールを組み込む（連結する）場合

ご自身の Gradio コードに `video_compressor` をインポートするだけで、1 行で動画圧縮タブを連結できます：

```python
import gradio as gr
import video_compressor

with gr.Blocks() as my_app:
    with gr.Tabs():
        with gr.Tab("🎬 動画圧縮"):
            # 1行でUIコンポーネントとエンコード処理を埋め込み可能
            video_compressor.create_video_compress_tab()
            
        with gr.Tab("その他の機能"):
            # ご自身のアプリの他の機能
            ...

my_app.launch()
```

---

## ⚙️ バックグラウンド関数としての呼び出し例

Gradio UI を介さずに、Python スクリプトから直接動画エンコード関数を実行することもできます：

```python
import video_compressor

# 単一動画のエンコード
output_path, status_msg = video_compressor.compress_video(
    input_file_path="input_sample.mp4",
    cq=32,                  # 画質/CQ値 (数字が小さいほど高画質)
    preset="p6",            # NVENC プリセット (p1~p7)
    keep_metadata=True,     # メタデータ保持
    suffix="_av1"           # 出力ファイルの末尾文字
)

print(status_msg)
print(f"出力ファイル: {output_path}")
```

---

## 📄 ライセンス

MIT License
