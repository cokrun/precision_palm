>    @echo off
>    title Precision Palm Enterprise OS - Local Runner
>    color 0A
>    echo ==============================================================================
>    echo       PRECISION PALM ENTERPRISE OS : AUTOMATED LOCAL RUNNER (ZERO CONFIG)
>    echo ==============================================================================
>    echo.
>
>    cd /d "%~dp0"
>
>    python --version >nul 2>&1
>    if errorlevel 1 (
>        echo [ERROR] Python tidak terdeteksi di sistem PATH Windows!
>        echo Silakan unduh dan pasang Python 3.10+ dari python.org.
>        pause
>        exit /b 1
>    )
>
>    if not exist "venv\Scripts\activate.bat" (
>        echo [1/4] Membuat Virtual Environment Python baru di folder 'venv'...
>        python -m venv venv
>        if errorlevel 1 (
>            echo [ERROR] Gagal membuat virtual environment.
>            pause
>            exit /b 1
>        )
>    ) else (
>        echo [1/4] Virtual Environment 'venv' sudah tersedia.
>    )
>
>    echo [2/4] Mengaktifkan virtual environment...
>    call venv\Scripts\activate.bat
>
>    echo [3/4] Memeriksa dan memasang pustaka dari requirements.txt...
>    python -m pip install --upgrade pip >nul 2>&1
>    pip install -r requirements.txt
>
>    echo.
>    echo ==============================================================================
>    echo [4/4] MEMULAI SERVER WEB PRECISION PALM...
>    echo Buka peramban di: http://127.0.0.1:8000 (atau http://127.0.0.1:5000)
>    echo ==============================================================================
>    echo.
>    python app.py
>    pause
>