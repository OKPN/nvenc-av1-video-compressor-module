import os
import json
import tempfile
import subprocess
from pathlib import Path
import gradio as gr

VIDEO_EXTENSIONS = {".mp4", ".webm", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".m4v"}
CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"

CUSTOM_CSS = """
/* === 全体テーマ & ベーススタイリング === */
body, .gradio-container {
    background-color: #0b0e14 !important;
    color: #e2e8f0 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

/* ヘッダーカード */
.header-box {
    background: #161b26;
    border: 1px solid #232a3b;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
}
.header-box h1 {
    color: #ffffff;
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 4px;
}
.header-box p {
    color: #94a3b8;
    font-size: 0.9rem;
}

/* カードコンテナ */
.card-box {
    background: #161b26 !important;
    border: 1px solid #232a3b !important;
    border-radius: 12px !important;
    padding: 18px !important;
    margin-bottom: 16px !important;
}
.card-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.card-desc {
    font-size: 0.82rem;
    color: #94a3b8;
    margin-bottom: 12px;
}

/* オレンジメインボタン */
.orange-btn {
    background: linear-gradient(135deg, #f95700 0%, #e04800 100%) !important;
    color: #ffffff !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 14px 24px !important;
    box-shadow: 0 4px 14px rgba(249, 87, 0, 0.35) !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}
.orange-btn:hover {
    background: linear-gradient(135deg, #ff6600 0%, #f95700 100%) !important;
    box-shadow: 0 6px 20px rgba(249, 87, 0, 0.5) !important;
    transform: translateY(-1px);
}

/* ステータスカウンターカード */
.status-counter-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    background: #10141d;
    border-radius: 8px;
    padding: 14px;
    text-align: center;
}
.status-counter-item {
    display: flex;
    flex-direction: column;
    align-items: center;
}
.status-counter-label {
    font-size: 0.78rem;
    color: #94a3b8;
    margin-bottom: 4px;
}
.status-counter-val {
    font-size: 1.4rem;
    font-weight: 700;
}
.val-wait { color: #3b82f6; }
.val-proc { color: #f59e0b; }
.val-succ { color: #10b981; }
.val-err  { color: #ef4444; }

/* 特徴カードグリッド */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin-top: 12px;
}
.feature-card {
    background: #161b26;
    border: 1px solid #232a3b;
    border-radius: 10px;
    padding: 16px;
}
.feature-icon {
    font-size: 1.5rem;
    margin-bottom: 8px;
}
.feature-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 4px;
}
.feature-desc {
    font-size: 0.8rem;
    color: #94a3b8;
}

/* ガイドテキスト */
.guide-text {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 4px;
}

/* アコーディオン・タブの調整 */
.tab-nav {
    border-bottom: 1px solid #232a3b !important;
}
button.selected {
    border-bottom-color: #f95700 !important;
    color: #f95700 !important;
}
"""

def load_default_config():
    defaults = {
        "video_default_cq": 32,
        "video_default_preset": "p6",
        "video_default_suffix": "_compressed",
        "server_port": 7861,
        "auto_open_browser": True
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**defaults, **data}
        except Exception:
            pass
    return defaults

def save_config_data(new_values):
    cfg = load_default_config()
    cfg.update(new_values)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        return "✅ 設定を config.json に保存しました。"
    except Exception as e:
        return f"❌ 設定の保存に失敗しました: {e}"

def compress_video(input_file_path, cq=32, preset="p6", keep_metadata=True, suffix="_compressed", custom_output_dir=None):
    if not input_file_path or not os.path.exists(input_file_path):
        return None, "エラー: 入力ファイルが存在しません。"

    stem_name = Path(input_file_path).stem
    out_dir = custom_output_dir if custom_output_dir and os.path.exists(custom_output_dir) else tempfile.gettempdir()
    
    clean_suffix = suffix if suffix is not None else ""
    output_path = os.path.join(out_dir, f"{stem_name}{clean_suffix}.mp4")

    command = ["ffmpeg", "-y", "-i", input_file_path]

    if keep_metadata:
        command.extend(["-map_metadata", "0", "-movflags", "use_metadata_tags"])

    command.extend([
        "-c:v", "av1_nvenc",
        "-rc:v", "vbr",
        "-cq:v", str(int(cq)),
        "-preset", str(preset),
        "-c:a", "copy",
        output_path
    ])

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        in_size_mb = os.path.getsize(input_file_path) / (1024 * 1024)
        out_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        reduction = (1 - (out_size_mb / in_size_mb)) * 100 if in_size_mb > 0 else 0
        
        status_msg = f"サイズ: {in_size_mb:.2f}MB ➔ {out_size_mb:.2f}MB ({reduction:.1f}% 削減)"
        return output_path, status_msg
    except subprocess.CalledProcessError as e:
        err_msg = f"動画エンコードエラー: {e.stderr if e.stderr else str(e)}"
        print(err_msg)
        return None, f"❌ {err_msg}"
    except Exception as e:
        err_msg = f"予期せぬエラー: {str(e)}"
        print(err_msg)
        return None, f"❌ {err_msg}"


def collect_video_files(input_files):
    video_paths = []
    if not input_files:
        return video_paths

    if not isinstance(input_files, list):
        input_files = [input_files]

    for item in input_files:
        path_str = item.name if hasattr(item, "name") else str(item)
        p = Path(path_str)
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                    video_paths.append(str(f))
        elif p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS:
            video_paths.append(str(p))

    seen = set()
    unique_paths = []
    for vp in video_paths:
        if vp not in seen:
            seen.add(vp)
            unique_paths.append(vp)

    return unique_paths


def make_counter_html(wait=0, proc=0, succ=0, err=0):
    return f"""
    <div class="status-counter-grid">
        <div class="status-counter-item">
            <span class="status-counter-label">待ちファイル</span>
            <span class="status-counter-val val-wait">{wait}</span>
        </div>
        <div class="status-counter-item">
            <span class="status-counter-label">処理中</span>
            <span class="status-counter-val val-proc">{proc}</span>
        </div>
        <div class="status-counter-item">
            <span class="status-counter-label">完了</span>
            <span class="status-counter-val val-succ">{succ}</span>
        </div>
        <div class="status-counter-item">
            <span class="status-counter-label">エラー</span>
            <span class="status-counter-val val-err">{err}</span>
        </div>
    </div>
    """


def check_ffmpeg_installed():
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def create_video_compress_tab(config=None):
    if config is None:
        config = load_default_config()

    default_cq = config.get("video_default_cq", 32)
    default_preset = config.get("video_default_preset", "p6")
    default_suffix = config.get("video_default_suffix", "_compressed")

    with gr.Column():
        gr.HTML("""
        <div class="header-box">
            <h1>NVENC AV1 Video Compressor Module</h1>
            <p>他アプリへ連結・組み込み可能な動画一括圧縮コンポーネント (NVIDIA NVENC アクセラレーション)</p>
        </div>
        """)

        # FFmpeg 未インストール時のみ最上部に表示される警告＆インストールバナー
        is_ffmpeg_ok = check_ffmpeg_installed()
        with gr.Column(visible=not is_ffmpeg_ok, elem_classes=["card-box"]) as ffmpeg_alert_group:
            gr.Markdown("⚠️ **FFmpeg が未検出です。** 動画圧縮を実行するには FFmpeg のインストールが必要です。")
            with gr.Row():
                install_top_btn = gr.Button("⚡ FFmpegを今すぐ自動インストール (Winget)", elem_classes=["orange-btn"])
            install_top_log = gr.Textbox(label="インストールログ", lines=2, visible=False)

            def _install_ffmpeg_top(progress=gr.Progress()):
                progress(0.2, desc="WingetでFFmpegを自動インストール中...")
                try:
                    cmd = ["winget", "install", "-e", "--id", "Gyan.FFmpeg", "--accept-source-agreements", "--accept-package-agreements"]
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    out_msg = res.stdout if res.stdout else ""
                    if check_ffmpeg_installed():
                        progress(1.0, desc="インストール完了!")
                        # インストール成功したため警告バナーを完全非表示(消す)にする
                        return gr.update(visible=False), gr.update(visible=False, value="")
                    else:
                        return gr.update(visible=True), gr.update(visible=True, value=f"⚠️ インストール結果:\n{out_msg}\n{res.stderr}")
                except Exception as e:
                    return gr.update(visible=True), gr.update(visible=True, value=f"❌ エラー: {str(e)}")

            install_top_btn.click(
                fn=_install_ffmpeg_top,
                outputs=[ffmpeg_alert_group, install_top_log]
            )

        with gr.Row():
            with gr.Column(scale=1, elem_classes=["card-box"]):
                gr.HTML('<div class="card-title">① 入力動画を選択</div><div class="card-desc">複数ファイル選択・フォルダドラッグ＆ドロップ対応</div>')
                vid_in = gr.File(
                    label="動画ファイルまたはフォルダをここにドロップ",
                    file_count="multiple"
                )

            with gr.Column(scale=1, elem_classes=["card-box"]):
                gr.HTML('<div class="card-title">② 変換済みファイル一覧</div><div class="card-desc">複数変換時は先頭の ZIP でまとめて一括保存できます</div>')
                vid_out = gr.File(
                    label="変換完了ファイル",
                    file_count="multiple"
                )

        with gr.Row():
            with gr.Column(scale=1, elem_classes=["card-box"]):
                gr.HTML('<div class="card-title">処理ステータス</div>')
                counter_html = gr.HTML(value=make_counter_html(0, 0, 0, 0))

            with gr.Column(scale=1, elem_classes=["card-box"]):
                gr.HTML('<div class="card-title">削減レポート</div>')
                status_box = gr.Textbox(label="ログ", value="圧縮実行後にレポートが表示されます", lines=3, interactive=False)

        with gr.Accordion("⚙️ 詳細パラメータ設定", open=False, elem_classes=["card-box"]):
            with gr.Row():
                cq_slider = gr.Slider(
                    minimum=1, maximum=51, value=default_cq, step=1,
                    label="画質 / CQ値 (おすすめ: 28-35 高画質, 35-45 標準)"
                )
                preset_radio = gr.Radio(
                    choices=["p1", "p2", "p3", "p4", "p5", "p6", "p7"],
                    value=default_preset,
                    label="NVENC プリセット (p1=最速 ~ p7=最高画質)"
                )
            with gr.Row():
                keep_meta_chk = gr.Checkbox(
                    value=True,
                    label="ComfyUI等のワークフロー・メタデータを保持する"
                )
                suffix_input = gr.Textbox(
                    value=default_suffix,
                    label="出力ファイルの末尾サフィックス (例: _compressed, _av1)"
                )

        vid_btn = gr.Button("一括 AV1 エンコード開始", elem_classes=["orange-btn"])

        def _handle_batch_compress(input_files, cq, preset, keep_meta, suffix, progress=gr.Progress()):
            if not input_files:
                return None, "動画ファイルまたはフォルダを選択してください。", make_counter_html(0, 0, 0, 0)

            target_videos = collect_video_files(input_files)
            total_count = len(target_videos)

            if total_count == 0:
                return None, "対象の動画ファイル (.mp4, .webm, .mov, .mkv 等) が見つかりませんでした。", make_counter_html(0, 0, 0, 0)

            output_files = []
            success_count = 0
            err_count = 0
            logs = []

            for i, video_path in enumerate(target_videos):
                filename = Path(video_path).name
                wait_left = total_count - i - 1
                progress((i / total_count), desc=f"変換中 ({i+1}/{total_count}): {filename}")

                # 処理中のカウンター更新
                out_path, msg = compress_video(
                    video_path,
                    cq=cq,
                    preset=preset,
                    keep_metadata=keep_meta,
                    suffix=suffix
                )
                if out_path:
                    output_files.append(out_path)
                    success_count += 1
                    logs.append(f"✅ {filename}: {msg}")
                else:
                    err_count += 1
                    logs.append(f"❌ {filename}: {msg}")

            progress(1.0, desc="変換完了!")
            
            # 複数ファイル変換完了時は ZIP アーカイブを自動作成してダウンロード一覧の先頭に追加
            final_outputs = []
            if len(output_files) > 1:
                zip_path = os.path.join(tempfile.gettempdir(), "compressed_videos_all.zip")
                try:
                    import zipfile
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        for file_p in output_files:
                            zipf.write(file_p, arcname=Path(file_p).name)
                    final_outputs.append(zip_path)
                except Exception as zip_e:
                    print(f"ZIP作成エラー: {zip_e}")
            
            final_outputs.extend(output_files)

            summary_header = f"🎉 一括変換完了! (成功: {success_count} / {total_count} 件)\n" + ("-" * 50) + "\n"
            final_status = summary_header + "\n".join(logs)
            final_counter_html = make_counter_html(0, 0, success_count, err_count)

            return final_outputs, final_status, final_counter_html

        vid_btn.click(
            fn=_handle_batch_compress,
            inputs=[vid_in, cq_slider, preset_radio, keep_meta_chk, suffix_input],
            outputs=[vid_out, status_box, counter_html]
        )

    return {
        "vid_in": vid_in,
        "vid_out": vid_out,
        "vid_btn": vid_btn
    }


def create_video_config_tab(config=None, save_func=None, is_embedded=False, restart_func=None):
    if config is None:
        config = load_default_config()

    with gr.Column():
        with gr.Row():
            gr.HTML("""
            <div style="margin-bottom: 12px;">
                <h2 style="font-size: 1.4rem; font-weight: 700; color: #ffffff; margin-bottom: 4px;">⚙️ 設定</h2>
                <p style="font-size: 0.88rem; color: #94a3b8;">アプリの動作や圧縮初期設定をカスタマイズします</p>
            </div>
            """)
            save_btn = gr.Button("💾 設定を保存", elem_classes=["orange-btn"])
            if not is_embedded and restart_func:
                restart_btn = gr.Button("♻️ アプリを再起動", variant="stop")

        save_msg = gr.Markdown("")

        with gr.Column(elem_classes=["card-box"]):
            gr.HTML('<div class="card-title">🎛️ 圧縮設定</div><div class="card-desc">デフォルトの画質とエンコード設定を行います</div>')
            with gr.Row():
                cfg_cq = gr.Slider(
                    minimum=1, maximum=51,
                    value=config.get("video_default_cq", 32), step=1,
                    label="デフォルト画質 / CQ値"
                )
            gr.HTML('<div class="guide-text">おすすめ: 28-35 (高画質) / 35-45 (標準) / 45以上 (低画質)</div>')

            with gr.Row():
                cfg_preset = gr.Radio(
                    choices=["p1", "p2", "p3", "p4", "p5", "p6", "p7"],
                    value=config.get("video_default_preset", "p6"),
                    label="デフォルト NVENC プリセット"
                )
            gr.HTML('<div class="guide-text">高速 (低圧縮: p1〜p3)  ←─────  標準 (p4)  ─────→  遅い・最高品質 (p5〜p7)</div>')

        with gr.Column(elem_classes=["card-box"]):
            card_title = "📁 出力設定" if is_embedded else "📁 出力・アプリ起動設定"
            card_desc = "出力ファイルの保存設定を行います" if is_embedded else "出力ファイルやアプリ起動時の動作を設定します"
            gr.HTML(f'<div class="card-title">{card_title}</div><div class="card-desc">{card_desc}</div>')
            with gr.Row():
                cfg_suffix = gr.Textbox(
                    value=config.get("video_default_suffix", "_compressed"),
                    label="出力ファイルの末尾サフィックス (元のファイル名の後に追加されます)"
                )
                cfg_port = gr.Number(
                    value=config.get("server_port", 7861),
                    label="初期起動ポート (占有時は+1ずつ順次自動試行)",
                    precision=0,
                    visible=not is_embedded
                )
            with gr.Row(visible=not is_embedded):
                cfg_auto_browser = gr.Checkbox(
                    value=config.get("auto_open_browser", True),
                    label="アプリ起動時に自動でブラウザを開く (http://localhost:ポート)",
                    visible=not is_embedded
                )
            with gr.Row():
                cfg_auto_delete = gr.Checkbox(
                    value=config.get("auto_delete_original_on_compress", False),
                    label="🗑️ 圧縮成功時に元動画を削除 (Windowsゴミ箱へ移動)"
                )


        def _on_save(cq, preset, suffix, port, auto_browser, auto_delete):
            new_cfg = {
                "video_default_cq": int(cq),
                "video_default_preset": preset,
                "video_default_suffix": suffix,
                "server_port": int(port),
                "auto_open_browser": bool(auto_browser),
                "auto_delete_original_on_compress": bool(auto_delete)
            }
            if save_func:
                msg = save_func(new_cfg)
            else:
                msg = save_config_data(new_cfg)
            return f"{msg}"

        save_btn.click(
            fn=_on_save,
            inputs=[cfg_cq, cfg_preset, cfg_suffix, cfg_port, cfg_auto_browser, cfg_auto_delete],
            outputs=save_msg
        )

        if not is_embedded and restart_func:
            def _on_restart(cq, preset, suffix, port, auto_browser, auto_delete):
                _on_save(cq, preset, suffix, port, auto_browser, auto_delete)
                restart_func()
                return "♻️ アプリを再起動しています..."

            restart_btn.click(
                fn=_on_restart,
                inputs=[cfg_cq, cfg_preset, cfg_suffix, cfg_port, cfg_auto_browser, cfg_auto_delete],
                outputs=save_msg
            )

        with gr.Column(elem_classes=["card-box"]):
            gr.HTML('<div class="card-title">🖥️ システム環境チェック & FFmpeg管理</div><div class="card-desc">FFmpegの状態を確認・管理します</div>')
            ffmpeg_status = gr.Textbox(label="FFmpegの検出状態", value="確認中...", interactive=False)
            with gr.Row():
                check_btn = gr.Button("🔄 検出テスト")
                install_btn = gr.Button("⚡ インストール (Winget)", variant="secondary")
                update_btn = gr.Button("⬆️ 最新版へアップデート (Winget)", variant="secondary")

            install_log = gr.Textbox(label="実行ログ", lines=4, interactive=False)

        def _get_ffmpeg_state():
            try:
                res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
                if res.returncode == 0:
                    first_line = res.stdout.splitlines()[0] if res.stdout else "検出完了"
                    status_str = f"🟢 FFmpegが正常に利用可能です ({first_line})"
                    btn_update = gr.update(value="🗑️ アンインストール (Winget)", variant="stop")
                    return True, status_str, btn_update
            except Exception:
                pass
            
            status_str = "🔴 FFmpegが見つかりません"
            btn_update = gr.update(value="⚡ インストール (Winget)", variant="secondary")
            return False, status_str, btn_update

        def _on_check():
            _, status_str, btn_update = _get_ffmpeg_state()
            return status_str, btn_update

        def _toggle_install_uninstall(progress=gr.Progress()):
            is_installed, _, _ = _get_ffmpeg_state()
            
            if is_installed:
                progress(0.2, desc="WingetでFFmpegをアンインストール中...")
                try:
                    cmd = ["winget", "uninstall", "-e", "--id", "Gyan.FFmpeg", "--accept-source-agreements"]
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    out_msg = res.stdout if res.stdout else ""
                    progress(1.0, desc="アンインストール完了")
                    _, status_str, btn_update = _get_ffmpeg_state()
                    return status_str, f"🗑️ アンインストール処理完了:\n{out_msg}", btn_update
                except Exception as e:
                    _, status_str, btn_update = _get_ffmpeg_state()
                    return status_str, f"❌ アンインストール実行エラー: {str(e)}", btn_update
            else:
                progress(0.2, desc="WingetでFFmpegを自動インストール中...")
                try:
                    cmd = ["winget", "install", "-e", "--id", "Gyan.FFmpeg", "--accept-source-agreements", "--accept-package-agreements"]
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    out_msg = res.stdout if res.stdout else ""
                    progress(1.0, desc="インストール完了")
                    _, status_str, btn_update = _get_ffmpeg_state()
                    return status_str, f"✅ インストール処理完了:\n{out_msg}", btn_update
                except Exception as e:
                    _, status_str, btn_update = _get_ffmpeg_state()
                    return status_str, f"❌ インストール実行エラー: {str(e)}", btn_update

        def _update_ffmpeg(progress=gr.Progress()):
            progress(0.2, desc="WingetでFFmpegの最新アップデートを確認・実行中...")
            try:
                cmd = ["winget", "upgrade", "-e", "--id", "Gyan.FFmpeg", "--accept-source-agreements", "--accept-package-agreements"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                _, status_str, btn_update = _get_ffmpeg_state()
                out_msg = res.stdout if res.stdout else ""
                if "no applicable upgrade found" in out_msg.lower() or "利用可能なアップグレードはありません" in out_msg:
                    progress(1.0, desc="すでに最新版です!")
                    return status_str, f"ℹ️ すでに最新版のFFmpegがインストールされています:\n{out_msg}", btn_update
                elif res.returncode == 0 or "successfully installed" in out_msg.lower() or "成功" in out_msg:
                    progress(1.0, desc="アップデート完了!")
                    return status_str, f"✅ FFmpegの最新版へのアップデートが完了しました:\n{out_msg}", btn_update
                else:
                    return status_str, f"⚠️ Wingetアップデート結果:\n{out_msg}\n{res.stderr}", btn_update
            except Exception as e:
                _, status_str, btn_update = _get_ffmpeg_state()
                return status_str, f"❌ アップデート実行エラー: {str(e)}", btn_update

        check_btn.click(fn=_on_check, outputs=[ffmpeg_status, install_btn])
        install_btn.click(fn=_toggle_install_uninstall, outputs=[ffmpeg_status, install_log, install_btn])
        update_btn.click(fn=_update_ffmpeg, outputs=[ffmpeg_status, install_log, install_btn])

        initial_status, initial_btn_update = _on_check()
        ffmpeg_status.value = initial_status


def create_video_compressor_app(config=None, save_func=None, title="NVENC AV1 Video Compressor Module", restart_func=None):
    if config is None:
        config = load_default_config()

    try:
        demo = gr.Blocks(title=title, css=CUSTOM_CSS)
    except Exception:
        demo = gr.Blocks(title=title)

    with demo:
        with gr.Tabs():
            with gr.Tab("🎬 動画一括圧縮"):
                create_video_compress_tab(config)
            with gr.Tab("⚙️ 設定"):
                create_video_config_tab(config, save_func, is_embedded=False, restart_func=restart_func)

    return demo
