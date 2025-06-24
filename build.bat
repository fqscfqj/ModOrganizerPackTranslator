@echo off
REM 设置控制台编码为UTF-8
chcp 65001 >nul
REM 设置环境变量确保UTF-8编码
set PYTHONIOENCODING=utf-8

echo ====================================
echo    Mod翻译工具
echo ====================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误: 未找到Python，请确保已安装Python并添加到PATH
    pause
    exit /b 1
)

REM 检查是否存在虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo 检测到虚拟环境，正在激活...
    call .venv\Scripts\activate.bat
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ 虚拟环境激活失败
        pause
        exit /b 1
    )
) else (
    echo 未检测到虚拟环境，使用系统Python环境
)

echo.
echo 正在安装/更新依赖包...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 依赖包安装失败
    pause
    exit /b 1
)

echo.
echo 正在清理之前的编译文件...
if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "*.spec" del /q "*.spec" >nul 2>&1

echo.
echo 正在编译程序...
pyinstaller --onefile --windowed --name "ModTranslator" --clean --hidden-import=customtkinter --hidden-import=tkinterdnd2 --hidden-import=py7zr --hidden-import=rarfile --hidden-import=openai main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 编译成功！
    echo 📁 可执行文件位置: dist\ModTranslator.exe
    
    REM 检查文件是否真的存在
    if exist "dist\ModTranslator.exe" (
        echo ✅ 文件验证成功
        echo 📊 文件大小: 
        dir "dist\ModTranslator.exe" | findstr "ModTranslator.exe"
    ) else (
        echo ❌ 警告: 编译报告成功但未找到可执行文件
    )
    
    echo.
    echo 按任意键打开dist文件夹...
    pause >nul
    explorer dist
) else (
    echo.
    echo ❌ 编译失败！错误代码: %ERRORLEVEL%
    echo.
    echo 可能的解决方案:
    echo 1. 检查所有依赖是否正确安装
    echo 2. 确保main.py文件存在且无语法错误
    echo 3. 尝试重新安装pyinstaller: pip install --upgrade pyinstaller
    echo.
    pause
) 