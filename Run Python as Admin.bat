@echo off
setlocal

FSUTIL dirty query %SystemDrive% >nul
if [%1] == [] (
    echo Drag and drop the python app you wish to run onto this batch file.
    echo Do not drop it onto this window, drop it on this file in the folder.
    pause
    exit /B
)

if %errorlevel% EQU 0 goto START

WHERE pythonw
IF %errorlevel% NEQ 0 (
    echo Could not locate pythonw. Make sure python is installed.
    echo If it is installed, make sure python is in your PATH variable.
    pause
    exit /B
)

set _batchFile=%~f0
set _Args=%*
set _batchFile=""%_batchFile:"=%""
set _Args=%_Args:"=""%

echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\run_mek_as_admin.vbs"
echo UAC.ShellExecute "cmd", "/c ""%_batchFile% %_Args%""", "", "runas", 0 >> "%temp%\run_mek_as_admin.vbs"
cscript "%temp%\run_mek_as_admin.vbs"
exit /B

:START
cd /d %~dp0
pythonw %1