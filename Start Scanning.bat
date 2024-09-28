@echo off
:: Check for permissions
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

:: If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

echo Starting YOLOv8 Object Detection...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python and try again.
    pause
    exit /b 1
)

:: Display a simple progress indicator while checking for updates
echo Checking for software updates...
for /L %%i in (1,1,10) do (
    echo|set /p="."
    timeout /t 1 >nul
)
echo.

:: Suppress pip output
echo Updating dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install --upgrade torch torchvision ultralytics opencv-python >nul 2>&1

:: Set the script name
set "SCRIPT_NAME=yolov8_person_detection.py"

:: Check if the script exists
if not exist "%SCRIPT_NAME%" (
    echo Error: %SCRIPT_NAME% not found in the current directory.
    echo Please ensure your YOLOv8 object detection script is in the same folder as this batch file.
    pause
    exit /b 1
)

:: Run the Python script
echo Running %SCRIPT_NAME%...
python "%SCRIPT_NAME%"

:: If the script exits, pause to show any error messages
pause
