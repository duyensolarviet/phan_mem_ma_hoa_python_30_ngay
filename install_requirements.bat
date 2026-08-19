@echo off
chcp 65001 >nul
title 📦 CÀI ĐẶT THƯ VIỆN BỔ TRỢ - PYTHON TOOL PROTECTOR
echo ========================================================
echo  ĐANG CÀI ĐẶT CÁC THƯ VIỆN CẦN THIẾT TỪ REQUIREMENTS.TXT
echo ========================================================
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
if %errorlevel% equ 0 (
    echo [OK] Cài đặt thư viện thành công 100%!
    echo Bạn có thể khởi động công cụ bằng CHAY_MAIN.bat
) else (
    echo [LỖI] Đã xảy ra lỗi trong quá trình cài đặt thư viện.
)
echo.
pause
