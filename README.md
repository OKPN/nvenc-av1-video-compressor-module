# NVENC AV1 Video Compressor Module

他アプリへの組込み・連結およびリモート利用を前提として設計された、NVIDIA NVENC ハードウェアアクセラレーション対応の超高速 AV1 動画一括圧縮モジュール ＆ Web UI アプリです。

---

## 📌 重要な前提条件

- **対応 GPU**: **NVIDIA GeForce RTX 40シリーズ以降** (Ada Lovelace 世代以降: RTX 4060 / 4070 / 4080 / 4090 / RTX Laptop GPU 等) または **AV1 NVENC エンコードに対応した NVIDIA GPU**
  - ※ RTX 30シリーズ以前や AMD / Intel GPU、CPU のみの環境では `av1_nvenc` エンコーダが動作しません。
- **動作環境**: Windows 10 / 11
- **必須ツール**: FFmpeg (AV1 NVENC 対応版。※ アプリの設定画面または起動バッチからワンクリックで自動インストール可能)
- **Python**: Python 3.10 以上

---

## 🚀 特長

1. **他アプリへの簡単な組み込み (Module Design)**:
   - バックエンド処理 (`compress_video`) や Gradio UI コンポーネント (`create_video_compress_tab`) が完全モジュール化されており、他の Python アプリや Gradio UI へ 1 行で連結・組み込みが可能です。
2. **LAN内や Tailscale 経由でのリモート利用に対応**:
   - `0.0.0.0` バインドで起動するため、メインPCで本アプリを立ち上げておけば、**Tailscale や LAN 内の他端末（Mac、iPhone、Android、他ノートPCなど）のブラウザからリモート接続**して動画を高速圧縮できます。
3. **ダブルクリック一発起動 (venv自動生成)**:
   - 付属の `start_video_compressor.bat` を実行するだけで、仮想環境 (`venv`) の作成、ライブラリのインストール、FFmpeg チェック、アプリ起動を全自動で行います。
4. **ComfyUI などのメタデータを完全維持**:
   - 生成 AI (ComfyUI / AnimateDiff / VideoCombine 等) のプロンプトやワークフロー情報（JSON メタデータ）を脱落させずに動画内へそのまま継承します (`-map_metadata 0`)。
5. **ポータブル＆簡単なアンインストール**:
   - システムやレジストリを汚さないクリーンな構造のため、不要になった場合は**フォルダごと削除するだけ**で完全にアンインストールできます。

---

## 💻 起動・使用方法

### 1. リポジトリの取得と初回起動（コマンド一括実行）

ターミナル（コマンドプロンプト / PowerShell）で以下のコマンドを実行するだけで、クローンから環境構築・アプリ起動まで完了します：

```bash
# 1. リポジトリのクローン ＆ フォルダ移動
git clone https://github.com/OKPN/nvenc-av1-video-compressor-module.git
cd nvenc-av1-video-compressor-module

# 2. 全自動起動バッチの実行 (初回は venv 自動作成 ＆ pip install を行います)
start_video_compressor.bat
```

```text
[バッチ処理が自動で行うこと]
1. 仮想環境 (venv) の自動作成
2. 必要なライブラリ (requirements.txt) の自動インストール
3. FFmpeg の検出と未検出時の全自動インストール (Winget)
4. Web UI アプリの自動起動 (http://localhost:7865)
```

起動後、ブラウザで `http://localhost:7865` にアクセスしてご利用ください。

*(※ バッチファイルを使わずコマンドラインで手動起動したい場合)*
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_video_compressor.py
```

---

### 2. LAN内・Tailscale 経由で他端末から使う場合

メインPC（NVIDIA GPU搭載機）でアプリを起動した状態で、他端末のブラウザから以下のアドレスにアクセスします：

- **LAN内**: `http://[メインPCのローカルIP]:7865`
- **Tailscale経由**: `http://[メインPCのTailscale-IP]:7865`

スマホや Mac など、NVIDIA GPU が入っていない端末からでもメインPCの NVENC パワーを使って超高速圧縮が可能です。

---

### 3. 他の Gradio アプリにモジュールとして組み込む場合

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
            # ご自身のアプリの機能
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
    suffix="_compressed"    # 出力ファイルの末尾文字
)

print(status_msg)
```

---

## 🗑️ アンインストール方法

本アプリはレジストリやシステム環境を一切変更しないポータブル設計です。
不要になった場合は、**本アプリのフォルダ全体をそのまま手動で削除（ごみ箱へ移動）するだけ** で完全にアンインストールが完了します。

---

## 📄 ライセンス

[MIT License](LICENSE)
