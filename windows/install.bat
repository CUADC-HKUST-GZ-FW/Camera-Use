@echo off
REM 海康威视相机控制程序 - Windows安装脚本

echo 海康威视相机控制程序 - Windows安装脚本
echo ==========================================

echo 检查Python版本...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version

echo.
echo 安装Python依赖...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo 警告: 某些包安装失败，尝试使用镜像源...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
)

echo.
echo 检查海康威视SDK...
set SDK_PATHS[0]="C:\Program Files\MVS"
set SDK_PATHS[1]="C:\Program Files (x86)\MVS"
set SDK_PATHS[2]="D:\MVS"

set SDK_FOUND=0
for %%p in (%SDK_PATHS[0]% %SDK_PATHS[1]% %SDK_PATHS[2]%) do (
    if exist %%p (
        echo 找到SDK: %%p
        set SDK_FOUND=1
        set SDK_PATH=%%p
        goto :found
    )
)

:found
if %SDK_FOUND%==0 (
    echo 警告: 未找到海康威视SDK
    echo.
    echo 请按照以下步骤安装SDK:
    echo 1. 从海康威视官网下载MVS软件包
    echo 2. 安装到 C:\Program Files\MVS\ 目录
    echo 3. 确保Python SDK路径正确
    echo.
    echo SDK下载地址:
    echo https://www.hikrobotics.com/cn/machinevision/service/download
    echo.
) else (
    echo SDK已安装
)

echo.
echo 安装完成!
echo ===========
echo.
echo 使用方法:
echo 1. 启动程序: start_camera.bat
echo 2. 或直接运行: python hikvision_camera_controller.py
echo.
echo 命令行选项:
echo   --calibration calibration_file  指定校准文件
echo   --capture [filename]            拍照模式
echo   --record [filename]             录像模式
echo   --preview                       预览模式
echo.
echo 示例:
echo   start_camera.bat --calibration ..\calibration\20250910_232046\calibration_result.json
echo   start_camera.bat --capture photo.jpg
echo   start_camera.bat --record video.avi --fps 25
echo.

if %SDK_FOUND%==0 (
    echo 注意: 请先安装海康威视SDK
)

pause
