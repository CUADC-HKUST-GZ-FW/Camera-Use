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
    echo "尝试自动设置环境变量..."
    
    # 自动检测和设置环境变量
    SDK_PATHS=("/opt/MVS" "/usr/local/MVS" "/home/$USER/MVS" "$(pwd)/MVS")
    ARCH=$(uname -m)
    
    for path in "${SDK_PATHS[@]}"; do
        if [ -d "$path" ]; then
            echo "找到SDK路径: $path"
            export MVS_SDK_PATH="$path"
            export MVCAM_COMMON_RUNENV="$path/lib"
            
            if [ "$ARCH" = "aarch64" ]; then
                # 检查aarch64库文件
                MAIN_LIB="$path/lib/aarch64/libMvCameraControl.so"
                if [ -f "$MAIN_LIB" ]; then
                    export LD_LIBRARY_PATH="$path/lib/aarch64:$path/lib:$LD_LIBRARY_PATH"
                    export PYTHONPATH="$path/Samples/aarch64/Python/MvImport:$PYTHONPATH"
                    echo "已设置ARM64架构环境变量 (专用路径)"
                else
                    # 回退到通用库路径
                    echo "警告: 未找到aarch64专用库，使用通用路径"
                    export LD_LIBRARY_PATH="$path/lib:$LD_LIBRARY_PATH"
                    # 尝试多个可能的Python路径
                    for py_path in "$path/Samples/aarch64/Python/MvImport" "$path/Samples/Python/MvImport" "$path/Python/MvImport"; do
                        if [ -d "$py_path" ]; then
                            export PYTHONPATH="$py_path:$PYTHONPATH"
                            echo "已设置ARM64架构环境变量 (通用路径): $py_path"
                            break
                        fi
                    done
                fi
            else
                export LD_LIBRARY_PATH="$path/lib/64:$path/lib/32:$path/lib:$LD_LIBRARY_PATH"
                export PYTHONPATH="$path/Samples/64/Python/MvImport:$PYTHONPATH"
                echo "已设置x86_64架构环境变量"
            fi
            
            echo "环境变量设置:"
            echo "  MVS_SDK_PATH=$MVS_SDK_PATH"
            echo "  MVCAM_COMMON_RUNENV=$MVCAM_COMMON_RUNENV"
            echo "  LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
            echo "  PYTHONPATH=$PYTHONPATH"
            break
        fi
    done
    
    if [ -z "$MVCAM_COMMON_RUNENV" ]; then
        echo "错误: 未找到SDK，请先安装海康威视SDK"
        echo "运行安装脚本: ./install.sh"
        exit 1
    fi
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
