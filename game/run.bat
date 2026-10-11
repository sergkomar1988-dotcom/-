@echo off
rem Запуск игры на Windows: двойной клик по файлу.
rem При первом запуске автоматически установится pygame (нужен Python 3.9+ с python.org).
cd /d "%~dp0"
py -m pip install -q -r requirements.txt
if errorlevel 1 (
  python -m pip install -q -r requirements.txt
)
py main.py
if errorlevel 1 (
  python main.py
)
pause
