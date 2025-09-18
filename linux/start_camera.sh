#!/bin/bash
# 海康威视相机控制程序启动脚本 - Linux版本

echo "海康威视相机控制程序 - Linux版本"
echo "================================"

# 检测系统架构和Jetson设备
ARCH=$(uname -m)
echo "系统架构: $ARCH"

if [ -f "/etc/nv_tegra_release" ]; then
    echo "✓ 检测到NVIDIA Jetson设备"
    JETSON_INFO=$(cat /etc/nv_tegra_release | head -1)
    echo "  $JETSON_INFO"
    
    # 检查Jetson性能模式
    if command -v nvpmodel &> /dev/null; then
        NVPMODEL_STATUS=$(nvpmodel -q 2>/dev/null | grep "NV Power Mode" || echo "状态未知")
        echo "  电源模式: $NVPMODEL_STATUS"
    fi
    
    # 温度监控提醒
    if command -v tegrastats &> /dev/null; then
        echo "  提示: 可使用 'tegrastats' 监控设备状态"
    fi
else
    echo "通用Linux系统"
fi

# 设置环境变量
if [ -f "./setup_env.sh" ]; then
    echo "加载SDK环境变量..."
    source ./setup_env.sh
else
    echo "警告: 未找到环境变量设置文件 setup_env.sh"
    echo "如果遇到SDK导入错误，请先运行安装脚本"
fi

# 检查Python依赖
echo "检查Python依赖..."
python3 -c "import cv2, numpy; print('✓ OpenCV和NumPy已安装')" 2>/dev/null || {
    echo "✗ 错误: OpenCV或NumPy未安装"
    echo "请运行以下命令安装:"
    echo "  pip3 install -r requirements.txt"
    echo "或运行安装脚本:"
    echo "  chmod +x install.sh && ./install.sh"
    exit 1
}

# 检查校准文件
CALIBRATION_FILE=""
if [ -f "../calibration/20250910_232046/calibration_result.json" ]; then
    CALIBRATION_FILE="../calibration/20250910_232046/calibration_result.json"
    echo "✓ 找到校准文件: $CALIBRATION_FILE"
elif [ -f "../calibration/20250910_232046/camera_parameters.xml" ]; then
    CALIBRATION_FILE="../calibration/20250910_232046/camera_parameters.xml"
    echo "✓ 找到校准文件: $CALIBRATION_FILE"
else
    echo "⚠ 警告: 未找到默认校准文件"
    echo "  程序将在无校准模式下运行"
fi

# 检查相机权限（仅对USB相机有效）
if lsusb | grep -q "2bdf"; then
    echo "✓ 检测到海康威视USB相机"
    # 检查权限
    if [ ! -w /dev/bus/usb ]; then
        echo "⚠ 警告: 可能需要USB权限"
        echo "  如果遇到权限错误，请运行:"
        echo "  sudo usermod -a -G plugdev $USER"
        echo "  然后重新登录"
    fi
fi

echo ""
echo "启动相机控制程序..."
echo "===================="

# 构建启动命令
CMD="python3 hikvision_camera_controller_linux.py"

# 如果找到校准文件，自动加载
if [ -n "$CALIBRATION_FILE" ]; then
    CMD="$CMD --calibration $CALIBRATION_FILE"
fi

# 添加用户参数
if [ $# -gt 0 ]; then
    CMD="$CMD $@"
fi

echo "执行命令: $CMD"
echo ""

# 启动程序
exec $CMD
