@echo off
chcp 65001 >nul
title Amazon Europe P&L Dashboard

cd /d "%~dp0"

echo =======================================
echo   Amazon Europe P&L Dashboard
echo =======================================
echo.

:: Перевіряємо чи встановлений Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python не знайдено.
    echo.
    echo     Встановіть Python з https://python.org/downloads
    echo     Важливо: під час встановлення поставте галочку
    echo     "Add Python to PATH"
    echo.
    echo     Після встановлення запустіть цей файл знову.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i знайдено
echo.

:: Встановлюємо залежності
echo [..] Перевіряємо залежності...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
echo [OK] Залежності встановлено
echo.

:: Запускаємо дашборд
echo [>>] Запускаємо дашборд...
echo      Браузер відкриється автоматично на http://localhost:8501
echo.
echo      Щоб зупинити - закрийте це вікно
echo.

python -m streamlit run app.py --server.headless false
pause
