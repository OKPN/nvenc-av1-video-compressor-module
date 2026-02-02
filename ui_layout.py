import gradio as gr
import json  # JSONパース用に必須
import encode_utils
import file_utils
import system_manager
import upscaler_utils
import comfy_utils

def create_ui(config, save_func, load_func):
    
    # リンクをMarkdown形式に変換するヘルパー関数
    def render_links(links_list):
        if not links_list:
            return "### 設定からアップローダーリンクを追加してください"
        md_list = [f"### [🔗 {l['name']}を開く ({l['url']})]({l['url']})" for l in links_list]
        return "\n".join(md_list)

    # 設定保存用の内部関数 (引数に links_json を追加)
    def on_save(url, input_dir, bat_path, wf_file, port, links_json):
        try:
            # 入力されたテキストをJSONとして読み込む
            links_list = json.loads(links_json)
            new_conf = {
                "comfy_url": url,
                "comfy_input_dir": input_dir,
                "launch_bat": bat_path,
                "upscaler_workflow_file": wf_file,
                "server_port": int(port),
                "uploader_links": links_list # リンク情報を追加
            }
            msg = save_func(new_conf)
            # 保存成功時に更新されたMarkdown表示を返す
            new_md = render_links(links_list)
            return msg, new_md, new_md
        except Exception as e:
            return f"❌ 保存失敗: JSONの形式が正しくありません。\n{str(e)}", gr.update(), gr.update()

    with gr.Blocks(title="MediaMatrix Station") as demo:
        gr.Markdown("# 🛠 MediaMatrix Station")
        
        with gr.Tabs():
            # --- 1. 画像処理 (互換/JXL) ---
            with gr.Tab("🖼 画像処理 (互換/JXL)"):
                with gr.Row():
                    with gr.Column():
                        img_in = gr.Image(label="入力画像", type="filepath")
                        mode_choice = gr.Radio(["標準最適化", "JXL変換"], value="標準最適化", label="モード")
                        
                        with gr.Group():
                            quality_sl = gr.Slider(1, 100, value=85, step=1, label="品質 (JPEG)")
                            convert_chk = gr.Checkbox(label="PNGをJPEGに変換する (推奨)", value=True)
                            dist_sl_single = gr.Slider(0.0, 4.0, value=1.0, step=0.1, label="Distance (0=無劣化)", visible=False)
                            effort_sl_single = gr.Slider(1, 9, value=7, step=1, label="Effort (速度優先=1, 圧縮優先=9)", visible=False)

                        img_btn = gr.Button("変換実行", variant="primary")
                        
                    with gr.Column():
                        img_out = gr.File(label="出力ファイル")
                        img_info = gr.Markdown("ステータス: 待機中")

                # 表示切替ロジック
                def update_mode_ui(mode):
                    if mode == "JXL変換":
                        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)
                    else:
                        return gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)

                mode_choice.change(update_mode_ui, inputs=[mode_choice], outputs=[quality_sl, convert_chk, dist_sl_single, effort_sl_single])
                
                def process_img(path, mode, q, convert, dist, effort):
                    if not path: return None, "画像を選択してください"
                    if mode == "JXL変換":
                        res, in_s, out_s, log = encode_utils.encode_image_jxl(path, distance=dist, effort=effort)
                    else:
                        res, in_s, out_s, log = encode_utils.optimize_image_standard(path, q, convert)
                    return res, f"**{log}**\nサイズ: {in_s} → {out_s}"

                img_btn.click(process_img, [img_in, mode_choice, quality_sl, convert_chk, dist_sl_single, effort_sl_single], [img_out, img_info])
                
                # 【追加】動的に書き換わるリンク表示エリア1
                links_display1 = gr.Markdown(render_links(config.get("uploader_links", [])))

            # --- 2. 動画変換 (AV1) ---
            with gr.Tab("🎬 動画変換 (AV1)"):
                with gr.Row():
                    vid_in = gr.Video(label="入力動画", sources="upload")
                    vid_btn = gr.Button("AV1エンコード開始", variant="primary")
                vid_out = gr.File(label="出力MP4")
                vid_btn.click(encode_utils.encode_video, inputs=vid_in, outputs=vid_out)
                
                # 【追加】動的に書き換わるリンク表示エリア2
                links_display2 = gr.Markdown(render_links(config.get("uploader_links", [])))

            # --- 3. JXL一括変換 ---
            with gr.Tab("📁 JXL一括変換"):
                gr.Markdown("### フォルダ内の画像を再帰的にJXLへ変換")
                with gr.Row():
                    in_dir = gr.Textbox(label="入力フォルダパス")
                    out_dir = gr.Textbox(label="出力フォルダパス")
                with gr.Row():
                    b_dist = gr.Slider(0.0, 4.0, value=1.0, step=0.1, label="Distance (0=無劣化)")
                    b_effort = gr.Slider(1, 9, value=7, step=1, label="Effort (速度優先=1, 圧縮優先=9)")
                
                b_strip = gr.Checkbox(label="メタデータを削除", value=False)
                batch_btn = gr.Button("一括変換実行", variant="primary")
                b_log = gr.Textbox(label="実行ログ", lines=10)
                b_summary = gr.Markdown("### 統計情報")
                
                batch_btn.click(encode_utils.batch_encode_jxl_recursive, [in_dir, out_dir, b_dist, b_effort, b_strip], [b_log, b_summary])

            # --- ui_layout.py の ⚡ TensorRT Upscaler タブ内 ---

            with gr.Tab("⚡ TensorRT Upscaler"):
                gr.Markdown("### ⚡ AI超解像アップスケーラー (TensorRT)")
                with gr.Row():
                    with gr.Column():
                    # typeを "filepath" に変更して元のパスを取得可能にする
                        u_in = gr.Image(label="入力画像", type="filepath") 
                        with gr.Row():
                            u_ratio = gr.Radio(["2x", "3x", "4x"], value="2x", label="倍率")
                            u_model = gr.Dropdown(["4x-AnimeSharp", "4x-UltraSharp"], value="4x-AnimeSharp")
                        u_btn = gr.Button("アップスケール実行", variant="primary")
                    with gr.Column():
                        u_out = gr.Image(label="プレビュー", interactive=False)
                        u_file = gr.File(label="ダウンロード (元の拡張子を維持)") # 確実な保存用
                        u_status = gr.Textbox(label="ステータス")

                def handle_upscale(img_path, r, m):
                    if not img_path: return None, None, "画像を選択してください"
                    from PIL import Image
                    img_obj = Image.open(img_path)
        
                    # original_pathとして入力パスを渡す
                    res_path, status = upscaler_utils.run_upscale(img_obj, r, m, load_func(), original_path=img_path)
                    return res_path, res_path, status # ImageとFileの両方にパスを渡す

                u_btn.click(handle_upscale, [u_in, u_ratio, u_model], [u_out, u_file, u_status])

            # --- 5. サーバー管理 ---
            with gr.Tab("⚙️ サーバ管理"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🛠 各種設定")
                        url_in = gr.Textbox(label="ComfyUI URL", value=config.get("comfy_url"))
                        dir_in = gr.Textbox(label="Input Dir", value=config.get("comfy_input_dir"))
                        bat_in = gr.Textbox(label="Bat Path", value=config.get("launch_bat"))
                        wf_in  = gr.Textbox(label="Workflow JSON", value=config.get("upscaler_workflow_file"))
                        port_in = gr.Number(label="Gradio Port (要再起動)", value=config.get("server_port", 7685), precision=0)
                        
                        # 【追加】JSON編集用のテキストボックス
                        links_json_in = gr.Textbox(
                            label="アップローダーリンク (JSON形式)", 
                            value=json.dumps(config.get("uploader_links", []), indent=2, ensure_ascii=False),
                            lines=5
                        )
                        
                        save_btn = gr.Button("設定保存")
                        save_msg = gr.Markdown("")
                    
                    with gr.Column():
                        status_text = gr.Textbox(label="ComfyUI 接続状態", value="確認中...", interactive=False)
                        refresh_btn = gr.Button("🔄 状態更新")
                        launch_btn = gr.Button("🚀 ComfyUI 起動", variant="primary")

                # 保存ボタンのクリックイベント (引数と出力を拡張)
                save_btn.click(
                    on_save, 
                    [url_in, dir_in, bat_in, wf_in, port_in, links_json_in], 
                    [save_msg, links_display1, links_display2]
                )
                refresh_btn.click(lambda: "🟢 稼働中" if system_manager.check_comfy_status() else "🔴 停止中", outputs=status_text)
                launch_btn.click(lambda: system_manager.launch_comfy(load_func()["launch_bat"]), outputs=status_text)

    return demo