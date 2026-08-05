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

## 💻 使い方・他アプリへの組込み

### Gradio アプリに組み込む場合

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
