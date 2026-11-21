@echo off
setlocal
if not exist .venv (
  python -m venv .venv
)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev,data]"
.venv\Scripts\python.exe scripts\bootstrap.py
