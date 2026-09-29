@echo off
rem Double-click this file to start the Auto Clicker (needs Python installed).
cd /d "%~dp0"
set "PY=python"
where py >nul 2>nul && set "PY=py"
%PY% -c "import pynput" 2>nul || %PY% -m pip install pynput
start "" %PY%w autoclicker.py
