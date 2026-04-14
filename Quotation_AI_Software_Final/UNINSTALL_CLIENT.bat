@echo off
setlocal

title Shreeji Ceramica - Uninstall Helper
color 0C

set "USER_UNINSTALL=%LOCALAPPDATA%\Programs\Shreeji Ceramica\Uninstall Shreeji Ceramica.exe"
set "MACHINE_UNINSTALL=%ProgramFiles%\Shreeji Ceramica\Uninstall Shreeji Ceramica.exe"
set "PORTABLE_DIR=%LOCALAPPDATA%\Shreeji Ceramica"

if exist "%USER_UNINSTALL%" (
    start "" "%USER_UNINSTALL%"
    endlocal
    exit /b 0
)

if exist "%MACHINE_UNINSTALL%" (
    start "" "%MACHINE_UNINSTALL%"
    endlocal
    exit /b 0
)

echo Proper Windows uninstaller was not found.
echo.
if exist "%PORTABLE_DIR%\Shreeji Ceramica.exe" (
    echo A portable copy was found here:
    echo %PORTABLE_DIR%
    echo.
    echo To remove it manually:
    echo 1. Close the app.
    echo 2. Delete this folder:
    echo    %PORTABLE_DIR%
    echo 3. Delete Desktop and Start Menu shortcuts if they still exist.
) else (
    echo If the app was installed using Setup, open:
    echo Settings ^> Apps ^> Installed apps ^> Shreeji Ceramica
)

echo.
pause
endlocal
