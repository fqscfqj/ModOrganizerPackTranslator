@echo off
setlocal
REM Set console code page to UTF-8
chcp 65001 >nul
REM Ensure Python uses UTF-8
set PYTHONIOENCODING=utf-8

echo ====================================
echo    ModOrganizerPackTranslator
echo ====================================
echo.

REM Check whether Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python was not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

REM Check whether a virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo Found virtual environment. Activating it...
    call .venv\Scripts\activate.bat
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to activate the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo No virtual environment found. Using system Python.
)

echo.
echo Installing or updating dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Cleaning previous build artifacts...
if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "build" rmdir /s /q "build" >nul 2>&1

echo.
echo Building application...
pyinstaller --clean ModOrganizerPackTranslator.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build succeeded.
    echo Executable: dist\ModOrganizerPackTranslator.exe
    
    REM Verify the output file exists
    if exist "dist\ModOrganizerPackTranslator.exe" (
        echo Output verification succeeded.
        echo File details:
        dir "dist\ModOrganizerPackTranslator.exe" | findstr "ModOrganizerPackTranslator.exe"
    ) else (
        echo WARNING: Build reported success but the executable was not found.
    )
    
    echo.
    echo Press any key to open the dist folder...
    pause >nul
    explorer dist
) else (
    echo.
    echo Build failed. Exit code: %ERRORLEVEL%
    echo.
    echo Possible fixes:
    echo 1. Verify that all dependencies are installed correctly.
    echo 2. Verify that main.py exists and has no syntax errors.
    echo 3. Try reinstalling PyInstaller: pip install --upgrade pyinstaller
    echo.
    pause
) 

endlocal
