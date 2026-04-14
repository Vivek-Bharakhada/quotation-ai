@echo off
setlocal

set "APP_DIR=%~dp0frontend\dist_client\win-unpacked"
set "APP_EXE=%APP_DIR%\Shreeji Ceramica.exe"
if not exist "%APP_EXE%" set "APP_EXE=%APP_DIR%\Quotation AI.exe"

echo ===================================================
echo  Quotation AI - Professional Installer Helper
echo ===================================================
echo.
echo  1. Checking finished software...
if not exist "%APP_EXE%" (
    echo  ERROR: Software not found. Please wait 1 more minute and try again.
    pause
    exit /b
)

echo  2. Installing Desktop and Start Menu Shortcuts...
set "SCRIPT=%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") >> "%SCRIPT%"

echo sLinkFile = "%USERPROFILE%\Desktop\Quotation AI.lnk" >> "%SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SCRIPT%"
echo oLink.TargetPath = "%APP_EXE%" >> "%SCRIPT%"
echo oLink.WorkingDirectory = "%APP_DIR%" >> "%SCRIPT%"
echo oLink.IconLocation = "%APP_EXE%, 0" >> "%SCRIPT%"
echo oLink.Save >> "%SCRIPT%"

echo sStartMenu = oWS.SpecialFolders("Programs") >> "%SCRIPT%"
echo sLinkFile = sStartMenu ^& "\Quotation AI.lnk" >> "%SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%SCRIPT%"
echo oLink.TargetPath = "%APP_EXE%" >> "%SCRIPT%"
echo oLink.WorkingDirectory = "%APP_DIR%" >> "%SCRIPT%"
echo oLink.IconLocation = "%APP_EXE%, 0" >> "%SCRIPT%"
echo oLink.Save >> "%SCRIPT%"

cscript /nologo "%SCRIPT%"
del "%SCRIPT%"

echo.
echo ===================================================
echo  SUCCESS! Look at your Desktop right now!
echo  Your "Quotation AI" icon is waiting for you.
echo ===================================================
pause
endlocal
