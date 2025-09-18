#!/bin/bash
# 海康威视相机控制程序 - Linux安装脚本

echo "海康威视相机控制程序 - Linux安装脚本"
echo "========================================"

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
elif type lsb_release >/dev/null 2>&1; then
    OS=$(lsb_release -si)
    VER=$(lsb_release -sr)
else
    echo "无法检测操作系统，请手动安装依赖"
    exit 1
fi

echo "检测到操作系统: $OS $VER"
echo "检测系统架构..."

# 检测系统架构
ARCH=$(uname -m)
echo "系统架构: $ARCH"

# 针对Jetson设备的特殊检测
if [ -f "/etc/nv_tegra_release" ]; then
    echo "检测到NVIDIA Jetson设备"
    JETSON_INFO=$(cat /etc/nv_tegra_release)
    echo "Jetson信息: $JETSON_INFO"
    IS_JETSON=true
else
    IS_JETSON=false
fi

# 安装系统依赖
echo ""
echo "安装系统依赖..."

if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    echo "使用 apt-get 安装依赖..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-dev
    
    # 针对Jetson设备的OpenCV安装
    if [ "$IS_JETSON" = true ]; then
        echo "Jetson设备：使用预安装的OpenCV..."
        # Jetson通常预装了OpenCV，检查是否存在
        python3 -c "import cv2; print('OpenCV version:', cv2.__version__)" 2>/dev/null || {
            echo "安装OpenCV for Jetson..."
            sudo apt-get install -y python3-opencv
        }
    else
        sudo apt-get install -y libopencv-dev python3-opencv
    fi
    
    sudo apt-get install -y build-essential cmake
    sudo apt-get install -y libusb-1.0-0-dev
    
    # Jetson特定的依赖
    if [ "$IS_JETSON" = true ]; then
        echo "安装Jetson特定依赖..."
        sudo apt-get install -y nvidia-l4t-camera
        sudo apt-get install -y v4l-utils
    fi
    
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Rocky"* ]]; then
    echo "使用 yum/dnf 安装依赖..."
    if command -v dnf &> /dev/null; then
        PKG_MGR="dnf"
    else
        PKG_MGR="yum"
    fi
    
    sudo $PKG_MGR update -y
    sudo $PKG_MGR install -y python3 python3-pip python3-devel
    sudo $PKG_MGR install -y opencv-devel python3-opencv
    sudo $PKG_MGR install -y gcc gcc-c++ make cmake
    sudo $PKG_MGR install -y libusb-devel
    
else
    echo "不支持的操作系统，请手动安装以下依赖:"
    echo "  - Python 3.7+"
    echo "  - pip"
    echo "  - OpenCV"
    echo "  - build-essential"
    echo "  - libusb开发库"
fi

# 检查Python版本
echo ""
echo "检查Python版本..."
python3 --version

# 安装Python依赖
echo ""
echo "安装Python依赖..."
pip3 install --user -r requirements.txt

# 检查海康威视SDK
echo ""
echo "检查海康威视SDK..."

# 根据架构设置SDK路径
if [ "$ARCH" = "aarch64" ]; then
    SDK_PATHS=(
        "/opt/MVS"
        "/usr/local/MVS"
        "/home/$USER/MVS"
    )
    SDK_ARCH_SUBDIR="aarch64"
    echo "ARM64架构：查找aarch64版本的SDK..."
else
    SDK_PATHS=(
        "/opt/MVS"
        "/usr/local/MVS"
        "/home/$USER/MVS"
    )
    SDK_ARCH_SUBDIR="64"
    echo "x86_64架构：查找64位版本的SDK..."
fi

SDK_FOUND=false
for path in "${SDK_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "找到SDK: $path"
        SDK_FOUND=true
        SDK_PATH=$path
        break
    fi
done

if [ "$SDK_FOUND" = false ]; then
    echo "警告: 未找到海康威视SDK"
    echo ""
    echo "请按照以下步骤安装SDK:"
    echo "1. 从海康威视官网下载Linux版本的MVS SDK"
    if [ "$ARCH" = "aarch64" ]; then
        echo "   注意：请下载ARM64 (aarch64) 版本的SDK"
        echo "   文件名通常为: MVS-*-Linux-aarch64-*.tar.gz"
    else
        echo "   注意：请下载x86_64版本的SDK" 
        echo "   文件名通常为: MVS-*-Linux-x86_64-*.tar.gz"
    fi
    echo "2. 解压SDK到 /opt/MVS/ 或 /usr/local/MVS/"
    echo "3. 运行SDK的安装脚本"
    echo "4. 设置环境变量"
    echo ""
    echo "SDK下载地址:"
    echo "https://www.hikrobotics.com/cn/machinevision/service/download"
    
    # 创建环境变量设置脚本
    cat > setup_env.sh << 'EOF'
#!/bin/bash
# 海康威视SDK环境变量设置
# 请根据实际SDK安装路径修改

# SDK安装路径（请根据实际情况修改）
export MVS_SDK_PATH="/opt/MVS"

# 设置环境变量
export MVCAM_COMMON_RUNENV="$MVS_SDK_PATH/lib"
export LD_LIBRARY_PATH="$MVS_SDK_PATH/lib/64:$MVS_SDK_PATH/lib/32:$LD_LIBRARY_PATH"
export PYTHONPATH="$MVS_SDK_PATH/Samples/64/Python:$PYTHONPATH"

echo "海康威视SDK环境变量已设置"
echo "SDK路径: $MVS_SDK_PATH"
echo "库路径: $MVCAM_COMMON_RUNENV"
EOF
    
    chmod +x setup_env.sh
    echo "已创建环境变量设置脚本: setup_env.sh"
    echo "安装SDK后，请运行: source setup_env.sh"
    
else
    echo "SDK已安装在: $SDK_PATH"
    
    # 自动设置环境变量
    echo "设置环境变量..."
    
    cat > setup_env.sh << EOF
#!/bin/bash
# 海康威视SDK环境变量设置

export MVS_SDK_PATH="$SDK_PATH"
export MVCAM_COMMON_RUNENV="$SDK_PATH/lib"

# 根据架构设置库路径
if [ "$ARCH" = "aarch64" ]; then
    export LD_LIBRARY_PATH="$SDK_PATH/lib/aarch64:$SDK_PATH/lib:$LD_LIBRARY_PATH"
    export PYTHONPATH="$SDK_PATH/Samples/aarch64/Python:$PYTHONPATH"
    echo "已设置ARM64架构的库路径"
else
    export LD_LIBRARY_PATH="$SDK_PATH/lib/64:$SDK_PATH/lib/32:$LD_LIBRARY_PATH"
    export PYTHONPATH="$SDK_PATH/Samples/64/Python:$PYTHONPATH"
    echo "已设置x86_64架构的库路径"
fi

echo "海康威视SDK环境变量已设置"
echo "SDK路径: $SDK_PATH"
echo "库路径: $MVCAM_COMMON_RUNENV"
echo "架构: $ARCH"
EOF
    
    chmod +x setup_env.sh
    
    # 设置当前会话的环境变量
    source setup_env.sh
fi

# 检查相机权限
echo ""
echo "设置USB相机权限..."

# 创建udev规则文件
if [ -w /etc/udev/rules.d/ ]; then
    cat > /tmp/99-mvs-camera.rules << 'EOF'
# 海康威视相机USB权限规则
# USB相机
SUBSYSTEM=="usb", ATTRS{idVendor}=="2bdf", MODE="0666", GROUP="plugdev"
# GigE相机通常不需要特殊权限，但确保网络配置正确
EOF
    
    sudo mv /tmp/99-mvs-camera.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    
    echo "已设置相机权限规则"
else
    echo "无法设置相机权限，请手动设置"
fi

# 创建启动脚本
echo ""
echo "创建启动脚本..."

cat > start_camera.sh << 'EOF'
#!/bin/bash
# 海康威视相机控制程序启动脚本

# 设置环境变量
if [ -f "./setup_env.sh" ]; then
    source ./setup_env.sh
fi

# 检查Python依赖
echo "检查Python依赖..."
python3 -c "import cv2, numpy; print('OpenCV和NumPy已安装')" || {
    echo "错误: OpenCV或NumPy未安装"
    echo "请运行: pip3 install -r requirements.txt"
    exit 1
}

# 启动程序
echo "启动相机控制程序..."
python3 hikvision_camera_controller_linux.py "$@"
EOF

chmod +x start_camera.sh

echo ""
echo "安装完成!"
echo "============"
echo ""
echo "使用方法:"
echo "1. 设置环境变量: source setup_env.sh"
echo "2. 启动程序: ./start_camera.sh"
echo "   或直接运行: python3 hikvision_camera_controller_linux.py"
echo ""
echo "命令行选项:"
echo "  --calibration calibration_file  指定校准文件"
echo "  --device 0                      指定设备索引"
echo "  --capture [filename]            拍照模式"
echo "  --record [filename]             录像模式"
echo "  --continuous [directory]        连续拍照模式"
echo ""
echo "示例:"
echo "  ./start_camera.sh --calibration ../calibration/20250910_232046/calibration_result.json"
echo "  ./start_camera.sh --capture photo.jpg"
echo "  ./start_camera.sh --record video.avi --fps 25"
echo ""

if [ "$SDK_FOUND" = false ]; then
    echo "注意: 请先安装海康威视SDK，然后运行 'source setup_env.sh'"
fi
