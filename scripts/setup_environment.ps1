>    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
>
>    Write-Host "`n==============================================================================" -ForegroundColor DarkGreen
>    Write-Host "      PRECISION PALM ENTERPRISE OS : POWERSHELL AUTOMATION" -ForegroundColor Cyan
>    Write-Host "==============================================================================" -ForegroundColor DarkGreen
>
>    $currentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
>    Set-Location $currentDir
>
>    try {
>        $pyVersion = & python --version 2>&1
>        Write-Host "[INFO] Terdeteksi: $pyVersion" -ForegroundColor Gray
>    } catch {
>        Write-Host "[ERROR] Python tidak ditemukan di PATH!" -ForegroundColor Red
>        exit 1
>    }
>
>    if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
>        Write-Host "[1/3] Membuat virtual environment baru (venv)..." -ForegroundColor Yellow
>        & python -m venv venv
>    }
>
>    Write-Host "[2/3] Mengaktifkan virtual environment..." -ForegroundColor Yellow
>    & ".\venv\Scripts\Activate.ps1"
>
>    Write-Host "[3/3] Menginstal dependensi requirements.txt..." -ForegroundColor Yellow
>    & python -m pip install --upgrade pip | Out-Null
>    & pip install -r requirements.txt
>
>    Write-Host "`n✓ ENVIRONMENT SIAP DIGUNAKAN!" -ForegroundColor Green
>    $startNow = Read-Host "Nyalakan server sekarang? (Y/N)"
>    if ($startNow -eq 'Y' -or $startNow -eq 'y' -or $startNow -eq '') {
>        & python app.py
>    }
>