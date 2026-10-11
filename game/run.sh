#!/bin/sh
# Запуск игры на Linux / macOS
cd "$(dirname "$0")" || exit 1
python3 -m pip install -q -r requirements.txt
python3 main.py
