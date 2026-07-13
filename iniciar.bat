@echo off
title Avaliacao PAP - Escola
cd /d "%~dp0"

set PYTHONDONTWRITEBYTECODE=1

echo ========================================
echo   Sistema de Avaliacao PAP
echo ========================================
echo.

REM Parar TODAS as instancias antigas do Streamlit (evita processos zombie com codigo antigo)
echo A parar instancias antigas...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*streamlit*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

REM Limpar todo o cache Python (evita modulos desatualizados)
for /d /r %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d" 2>nul
)

if exist ".venv\Scripts\streamlit.exe" (
    echo A iniciar com ambiente virtual...
    ".venv\Scripts\streamlit.exe" run streamlit_app.py
) else if exist ".venv\Scripts\python.exe" (
    echo A iniciar com ambiente virtual...
    ".venv\Scripts\python.exe" -m streamlit run streamlit_app.py
) else (
    echo A iniciar com Python do sistema...
    streamlit run streamlit_app.py
)

if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel iniciar.
    echo Verifique se Python e as dependencias estao instaladas:
    echo   pip install -r requirements.txt
    echo.
    pause
)
