@echo off
echo cd into script directory ...
cd /d %~dp0
echo Create .venv if it does not exist ...
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Upgrade pip ...
python -m pip install --upgrade pip
echo Install package ...
pip install -e .
echo Copy config.yaml if it does not exist ...
if not exist config.yaml (
    copy config.example.yaml config.yaml
)
echo Create desktop shortcut ...
pip install pywin32
python create_shortcut.py
echo Done.
pause