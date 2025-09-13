#!/bin/bash
# 海康威视相机控制程序 - Linux版本启动器

echo "海康威视相机控制程序 - Linux版本"
echo "========================================"

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINUX_DIR="$SCRIPT_DIR/linux"

# 检查Linux版本目录
if [ ! -d "$LINUX_DIR" ]; then
    echo "错误: 未找到Linux版本目录"
    echo "请确保 linux/ 目录存在"
    exit 1
fi

# 切换到Linux目录
cd "$LINUX_DIR"

# 检查程序文件
if [ ! -f "hikvision_camera_controller_linux.py" ]; then
    echo "错误: 未找到Linux版本程序文件"
    echo "请确保 linux/hikvision_camera_controller_linux.py 存在"
    exit 1
fi

echo "启动Linux版本相机控制程序..."

# 检查启动脚本是否存在
if [ -f "start_camera.sh" ]; then
    chmod +x start_camera.sh
    ./start_camera.sh "$@"
else
    # 直接运行Python程序
    python3 hikvision_camera_controller_linux.py "$@"
fi
