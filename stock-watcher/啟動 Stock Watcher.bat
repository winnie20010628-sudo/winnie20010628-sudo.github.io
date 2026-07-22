@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo 正在建立虛擬環境...
  python -m venv .venv
  if errorlevel 1 (
    echo 請先安裝 Python 3，並勾選 Add to PATH。
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate.bat
python -c "import httpx,bs4,lxml,pydantic" 2>nul
if errorlevel 1 (
  echo 正在安裝套件...
  pip install -r requirements.txt
)

echo 啟動 Stock Watcher...
python run.py
if errorlevel 1 pause
