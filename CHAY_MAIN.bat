@echo off
chcp 65001 >nul
title 🛡️ CONTROL CENTER - PYTHON TOOL PROTECTOR
python src/main.py
if %errorlevel% neq 0 (
    pause
)
