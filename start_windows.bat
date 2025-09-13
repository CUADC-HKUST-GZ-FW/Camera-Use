@echo off
REM 海康威视相机控制程序 - Windows版本启动器
echo 海康威视相机控制程序 - Windows版本
echo ========================================

cd /d "%~dp0\windows"

if not exist "hikvision_camera_controller.py" (
    echo 错误: 未找到Windows版本程序文件
    echo 请确保 windows\hikvision_camera_controller.py 存在
    pause
    exit /b 1
)

echo 启动Windows版本相机控制程序...
python hikvision_camera_controller.py %*

pause
