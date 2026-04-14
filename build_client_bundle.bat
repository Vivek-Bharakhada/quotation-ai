@echo off
setlocal

set "ROOT=%~dp0"
set "FINAL_DIR=%ROOT%Quotation_AI_Software_Final"
set "DIST_DIR=%ROOT%frontend\dist_client"
set "SETUP_EXE="
set "SETUP_NAME="
set "PORTABLE_EXE=%DIST_DIR%\win-unpacked\Shreeji Ceramica.exe"

echo ===================================================
echo   Quotation AI - Deep Structural Build
echo ===================================================
echo 0. Killing potential ghost processes...
taskkill /F /IM "Shreeji Ceramica.exe" /T /FI "STATUS eq RUNNING" 2>nul
taskkill /F /IM "Quotation AI.exe" /T /FI "STATUS eq RUNNING" 2>nul
taskkill /F /IM "backend_sidecar.exe" /T /FI "STATUS eq RUNNING" 2>nul

if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
echo 1. Building React Production Assets...
cd /d "%ROOT%frontend"
call npm run build
if errorlevel 1 goto :fail
echo 2. Syncing Electron Startup Files...
copy electron\main.js build\electron.js /Y >nul
copy electron\preload.js build\preload.js /Y >nul
if errorlevel 1 goto :fail
echo 3. Sanitizing Build Icons (Nuclear Fix)...
if exist "build\favicon.ico" del /q "build\favicon.ico"
echo 4. Generating Windows Installer (Setup)...
call npm run dist
if errorlevel 1 goto :fail
if exist "%DIST_DIR%\*Setup*.exe" (
    for %%F in ("%DIST_DIR%\*Setup*.exe") do (
        if not defined SETUP_EXE (
            set "SETUP_EXE=%%~fF"
            set "SETUP_NAME=%%~nxF"
        )
    )
)
echo 5. Refreshing deliverable folder...
if not exist "%FINAL_DIR%" mkdir "%FINAL_DIR%"
if exist "%FINAL_DIR%\win-unpacked" rmdir /s /q "%FINAL_DIR%\win-unpacked"
if exist "%DIST_DIR%\win-unpacked" robocopy "%DIST_DIR%\win-unpacked" "%FINAL_DIR%\win-unpacked" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul
if exist "%FINAL_DIR%\*Setup*.exe" for %%F in ("%FINAL_DIR%\*Setup*.exe") do del /q "%%~fF"
if exist "%SETUP_EXE%" copy "%SETUP_EXE%" "%FINAL_DIR%\" /Y >nul
echo ===================================================
if exist "%SETUP_EXE%" (
    echo  DONE! Your Installer is here: frontend\dist_client
    echo  Look for: %SETUP_NAME%
) else (
    if exist "%PORTABLE_EXE%" (
        echo  DONE! Updated desktop app is ready in: frontend\dist_client\win-unpacked
        echo  Open: Shreeji Ceramica.exe
    ) else (
        echo  ERROR: Installer was not generated. Check logs!
    )
)
if exist "%FINAL_DIR%\*Setup*.exe" (
    echo  Shareable package refreshed in: Quotation_AI_Software_Final
)
echo ===================================================
pause
endlocal
exit /b 0

:fail
echo ===================================================
echo  ERROR: Build failed. Check the terminal output above.
echo ===================================================
pause
endlocal
exit /b 1
