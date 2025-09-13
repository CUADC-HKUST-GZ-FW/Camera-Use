@echo off
echo =================================
echo 海康威视相机控制程序 - Windows版本
echo =================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查Python依赖...
python -c "import cv2, numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装Python依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 错误：依赖安装失败
        pause
        exit /b 1
    )
)

REM 启动程序
echo 启动相机控制程序...
echo.
python hikvision_camera_controller.py %*

pause
