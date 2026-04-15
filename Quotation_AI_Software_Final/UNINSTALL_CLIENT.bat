@echo off
setlocal
title Shreeji Ceramica - Uninstaller
color 0C

set "INSTALL_DIR=%LOCALAPPDATA%\Shreeji Ceramica"

echo.
echo  ===================================================
echo   Shreeji Ceramica - Uninstaller
echo  ===================================================
echo.
echo  This will remove Shreeji Ceramica from your computer.
echo  Press any key to continue or close this window to cancel.
pause >nul

taskkill /F /IM "Shreeji Ceramica.exe" /T 2>nul

if exist "%INSTALL_DIR%" (
    rmdir /s /q "%INSTALL_DIR%"
    echo  Software removed.
) else (
    echo  Software folder not found.
)

set "DESKTOP_LNK=%USERPROFILE%\Desktop\Shreeji Ceramica.lnk"
if exist "%DESKTOP_LNK%" del /q "%DESKTOP_LNK%" && echo  Desktop shortcut removed.

set "STARTMENU_LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Shreeji Ceramica.lnk"
if exist "%STARTMENU_LNK%" del /q "%STARTMENU_LNK%" && echo  Start Menu shortcut removed.

echo.
echo  ===================================================
echo   Uninstall complete!
echo  ===================================================
echo.
pause
endlocal
