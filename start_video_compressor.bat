@echo off
:: 文字コードをUTF-8に変更
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d %~dp0

set VENV_NAME=venv
set SCRIPT_NAME=run_video_compressor.py

title NVENC AV1 Video Compressor Module Launcher

echo ========================================================
echo   NVENC AV1 Video Compressor Module 起動ツール
echo ========================================================
echo.

:: 1. 仮想環境 (venv) の自動チェック＆作成
if exist "%VENV_NAME%" goto :CHECK_FFMPEG

echo [INFO] 初回起動: 仮想環境 (%VENV_NAME%) を作成しています...
python -m venv %VENV_NAME%
if errorlevel 1 (
    echo [ERROR] Python が見つからないか、venv の作成に失敗しました。
    echo Python 3.10 以上がインストールされているか確認してください。
    pause
    exit /b 1
)

echo [INFO] 必要なライブラリをインストールしています...
"%VENV_NAME%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_NAME%\Scripts\pip.exe" install -r requirements.txt
echo [INFO] 仮想環境の構築が完了しました！
echo.

:CHECK_FFMPEG
:: 2. FFmpeg のチェック
where ffmpeg >nul 2>nul
if %errorlevel% equ 0 goto :START_APP

echo [WARNING] FFmpeg が見つかりませんでした。
echo Winget を使用して FFmpeg (Gyan.FFmpeg) を自動インストールしますか？
set /p ASK_INSTALL="インストールしますか？ (y/n) > "

if /i "!ASK_INSTALL!"=="y" (
    echo [INFO] winget で FFmpeg をインストール中...
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
    echo.
    echo [INFO] インストールが完了しました。
) else (
    echo [INFO] FFmpeg の自動インストールをスキップしました。
    echo (※ Web UI の設定タブから後でインストールすることも可能です)
)

:START_APP
:: 3. アプリケーションの起動
echo.
echo [START] 仮想環境を使って %SCRIPT_NAME% を起動します...
echo.
"%VENV_NAME%\Scripts\python.exe" %SCRIPT_NAME%

pause
