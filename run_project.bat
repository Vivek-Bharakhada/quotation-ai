@echo off
setlocal

set "ROOT=%~dp0"

echo Updating search index with new products...
cd /d "%ROOT%backend"
REM python add_missing_showers.py

echo.
echo Starting Backend Server with auto-reload...
start "Quotation AI Backend" cmd /k "cd /d ""%ROOT%backend"" && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo Starting Frontend Dev Server for live updates...
start "Quotation AI Frontend" cmd /k "cd /d ""%ROOT%frontend"" && set ""BROWSER=none"" && npm start"

echo.
echo Waiting for frontend to come online...
timeout /t 10 /nobreak >nul

echo Starting Desktop App in live verify mode...
start "Quotation AI Desktop" cmd /k "cd /d ""%ROOT%frontend"" && npm run desktop:dev"

echo.
echo Live desktop flow is launching!
echo Backend API: http://localhost:8000
echo Frontend Dev Server: http://localhost:3000
echo Verify directly in the Electron app window.
pause
endlocal
