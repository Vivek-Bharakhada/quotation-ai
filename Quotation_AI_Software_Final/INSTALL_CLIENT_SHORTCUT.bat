@echo off
setlocal

title Shreeji Ceramica - Installer Launcher
color 0B

set "ROOT=%~dp0"
set "SETUP_EXE="
if exist "%ROOT%*Setup*.exe" (
    for %%F in ("%ROOT%*Setup*.exe") do (
        if not defined SETUP_EXE set "SETUP_EXE=%%~fF"
    )
)

echo.
echo  ===================================================
echo   Shreeji Ceramica - Installer Launcher
echo  ===================================================
echo.

if defined SETUP_EXE (
    echo  [1/2] Found Windows Setup installer.
    echo  [2/2] Launching installer...
    echo.
    echo  %SETUP_EXE%
    echo.
    start /wait "" "%SETUP_EXE%"
    echo.
    echo  Setup finished.
    echo  Launch the app from Desktop or Start Menu.
    echo  Uninstall: Settings ^> Apps ^> Installed apps ^> Shreeji Ceramica
    echo.
    pause
    endlocal
    exit /b 0
)

echo  [INFO] Setup EXE not found in this folder.
echo  Falling back to portable copy mode.
echo  Note: this fallback does not create a Windows uninstall entry.
echo.

if not exist "%ROOT%win-unpacked\Shreeji Ceramica.exe" (
    echo  [ERROR] Software files not found!
    echo  Keep either the Setup EXE or the "win-unpacked" folder next to this script.
    echo.
    pause
    endlocal
    exit /b 1
)

echo  [1/4] Copying software to your computer...
set "INSTALL_DIR=%LOCALAPPDATA%\Shreeji Ceramica"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
robocopy "%ROOT%win-unpacked" "%INSTALL_DIR%" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul

echo  [2/4] Creating Desktop shortcut...
set "SCRIPT=%TEMP%\qai_install_%RANDOM%.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%SCRIPT%"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Shreeji Ceramica.lnk" >> "%SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SCRIPT%"
echo oLink.TargetPath = "%INSTALL_DIR%\Shreeji Ceramica.exe" >> "%SCRIPT%"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%SCRIPT%"
echo oLink.IconLocation = "%INSTALL_DIR%\Shreeji Ceramica.exe, 0" >> "%SCRIPT%"
echo oLink.Description = "Shreeji Ceramica" >> "%SCRIPT%"
echo oLink.Save >> "%SCRIPT%"

echo  [3/4] Creating Start Menu shortcut...
echo sStartMenu = oWS.SpecialFolders("Programs") >> "%SCRIPT%"
echo sLinkFile = sStartMenu ^& "\Shreeji Ceramica.lnk" >> "%SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SCRIPT%"
echo oLink.TargetPath = "%INSTALL_DIR%\Shreeji Ceramica.exe" >> "%SCRIPT%"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%SCRIPT%"
echo oLink.IconLocation = "%INSTALL_DIR%\Shreeji Ceramica.exe, 0" >> "%SCRIPT%"
echo oLink.Description = "Shreeji Ceramica" >> "%SCRIPT%"
echo oLink.Save >> "%SCRIPT%"

cscript /nologo "%SCRIPT%"
del "%SCRIPT%" >nul 2>&1

echo  [4/4] Launching Shreeji Ceramica...
start "" "%INSTALL_DIR%\Shreeji Ceramica.exe"

echo.
echo  ===================================================
echo   Portable install complete.
echo   Uninstall: delete %INSTALL_DIR%
echo   Then remove Desktop and Start Menu shortcuts.
echo  ===================================================
echo.
pause
endlocal
