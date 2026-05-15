@echo off
echo Divera -> Smart Home wird gestartet...
cd /d "%~dp0"

:: Python suchen (verschiedene Installationswege)
set PYTHON=
where python >nul 2>&1 && set PYTHON=python
if "%PYTHON%"=="" where py >nul 2>&1 && set PYTHON=py
if "%PYTHON%"=="" where python3 >nul 2>&1 && set PYTHON=python3

if "%PYTHON%"=="" (
    echo.
    echo FEHLER: Python nicht gefunden!
    echo.
    echo Bitte Python 3.10+ installieren:
    echo   https://www.python.org/downloads/
    echo   - Haekchen bei "Add Python to PATH" setzen!
    echo.
    pause
    exit /b 1
)

echo Python gefunden: %PYTHON%

if not exist ".venv" (
    echo Erstelle virtuelle Umgebung...
    %PYTHON% -m venv .venv
    echo Installiere Abhaengigkeiten...
    .venv\Scripts\pip install -r requirements.txt
)

echo.
echo Server laeuft auf: http://localhost:5000
echo Mit Strg+C beenden.
echo.
start http://localhost:5000
.venv\Scripts\python app.py
pause
