@echo off
:: 文字コードをUTF-8に変更
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d %~dp0

:: --- 設定エリア ---
set VENV_NAME=venv
set PYTHON_SCRIPT=app.py
:: ------------------

title MediaMatrix Station Launcher

echo ========================================================
echo   MediaMatrix Station 起動ツール
echo ========================================================

:: 1. 仮想環境のチェック
if exist "%VENV_NAME%" goto :CHECK_FFMPEG

echo [INFO] 初回起動: 仮想環境を作成しています...
python -m venv %VENV_NAME%
if errorlevel 1 goto :ERROR_PYTHON

echo [INFO] ライブラリをインストールしています...
"%VENV_NAME%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_NAME%\Scripts\pip.exe" install -r requirements.txt
echo [INFO] 環境構築完了！

:CHECK_FFMPEG
:: 2. FFmpegのチェック
where ffmpeg >nul 2>nul
if %errorlevel% equ 0 goto :START_APP

echo.
echo [WARNING] 動画変換に必要な 'ffmpeg' が見つかりませんでした。
echo.
echo Winget (Windows標準機能) を使って自動インストールしますか？
echo ※ 「はい」を選ぶとインストールを試みます。
echo.
set /p ASK_INSTALL="インストールしますか？ (y/n) > "

if /i "!ASK_INSTALL!"=="y" (
    goto :INSTALL_FFMPEG
) else (
    echo.
    echo [INFO] インストールをスキップしました。
    goto :START_APP
)

:INSTALL_FFMPEG
echo.
echo [INFO] winget経由でFFmpeg (Gyan.FFmpeg) をインストールします...
echo ※ 途中で「変更を許可しますか？」と聞かれたら「はい」を押してください。
echo.
winget install -e --id Gyan.FFmpeg

echo.
echo ========================================================
echo  インストール処理が終了しました。
echo  設定を反映させるため、一度このウィンドウを閉じて
echo  もう一度バッチファイルをダブルクリックしてください。
echo ========================================================
pause
exit

:START_APP
:: 3. アプリケーションの起動
echo.
echo [START] 仮想環境を使って %PYTHON_SCRIPT% を起動します...
echo --------------------------------------------------------

:: 仮想環境の中のpythonを直接指名して実行
"%VENV_NAME%\Scripts\python.exe" %PYTHON_SCRIPT%

:: 終了時のエラーチェック
if errorlevel 1 goto :ERROR_APP

:: 正常終了
echo.
echo アプリケーションを終了しました。
pause
exit

:ERROR_PYTHON
echo.
echo --------------------------------------------------------
echo [ERROR] Python が見つからないか、実行に失敗しました。
echo.
echo ▼ 対処方法:
echo 1. Python 3.12 がインストールされているか確認してください。
echo 2. 未インストールの場合は、公式サイトから 3.12.x を入手してください。
echo    URL: https://www.python.org/downloads/windows/
echo.
echo ★重要★
echo インストーラー実行時、画面下の 
echo [Add Python to PATH] に必ずチェックを入れてください。
echo --------------------------------------------------------
pause
exit

:ERROR_APP
echo.
echo [ERROR] アプリが異常終了しました。
echo --------------------------------------------------------
echo もし「AttributeError: ... has no attribute 'Blocks'」が出る場合
echo → フォルダ内に「gradio.py」というファイルがあれば削除してください。
echo --------------------------------------------------------
pause
exit