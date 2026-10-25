@echo off
setlocal
title Precision Palm Enterprise OS - Local Runner
color 0A
echo ==============================================================================
echo       PRECISION PALM ENTERPRISE OS : AUTOMATED LOCAL RUNNER
echo ==============================================================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak terdeteksi di sistem PATH Windows!
    echo Silakan unduh dan pasang Python 3.10+ dari python.org.
    pause
    exit /b 1
)

if not exist "venv\Scripts\activate.bat" (
    echo [1/4] Membuat Virtual Environment Python baru di folder 'venv'...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Gagal membuat virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Virtual Environment 'venv' sudah tersedia.
)

echo [2/4] Mengaktifkan virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Gagal mengaktifkan virtual environment.
    pause
    exit /b 1
)

echo [3/4] Memasang pustaka dari requirements.txt...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Gagal memperbarui pip.
    pause
    exit /b 1
)
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Gagal memasang dependensi.
    pause
    exit /b 1
)

echo.
echo ==============================================================================
echo [4/4] MEMULAI SERVER WEB PRECISION PALM...
echo Buka peramban di: http://127.0.0.1:8080
echo ==============================================================================
echo.
python app.py
set "APP_EXIT_CODE=%ERRORLEVEL%"
pause
exit /b %APP_EXIT_CODE%