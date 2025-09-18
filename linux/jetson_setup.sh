#!/bin/bash
# Jetson Orin Nano 快速配置脚本
# 针对海康威视相机控制程序的优化设置

echo "=========================================="
echo "Jetson Orin Nano 相机程序快速配置脚本"
echo "=========================================="

# 检查是否为Jetson设备
if [ ! -f "/etc/nv_tegra_release" ]; then
    echo "错误: 这不是Jetson设备！"
    exit 1
fi

echo "✓ 检测到Jetson设备"
cat /etc/nv_tegra_release | head -1

# 检查架构
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
    echo "错误: 架构不匹配，期望aarch64，实际$ARCH"
    exit 1
fi

echo "✓ 架构确认: $ARCH"

# 1. 系统更新
echo ""
echo "1. 更新系统包..."
sudo apt-get update

# 2. 安装基础依赖
echo ""
echo "2. 安装基础依赖..."
sudo apt-get install -y python3 python3-pip python3-dev
sudo apt-get install -y build-essential cmake
sudo apt-get install -y libusb-1.0-0-dev
sudo apt-get install -y nvidia-l4t-camera
sudo apt-get install -y v4l-utils
sudo apt-get install -y jetson-stats

# 3. 检查OpenCV
echo ""
echo "3. 检查OpenCV安装..."
python3 -c "import cv2; print('✓ OpenCV version:', cv2.__version__)" 2>/dev/null || {
    echo "安装OpenCV..."
    sudo apt-get install -y python3-opencv
}

# 4. 安装Python依赖
echo ""
echo "4. 安装Python依赖..."
pip3 install numpy>=1.19.0

# 5. 性能优化
echo ""
echo "5. 应用性能优化..."

# 设置最大性能模式
echo "设置最大性能模式..."
sudo nvpmodel -m 0

# 锁定最大频率
echo "锁定最大CPU/GPU频率..."
sudo jetson_clocks

# 优化网络设置（如果有以太网）
if ip link show eth0 &>/dev/null; then
    echo "优化网络设置..."
    sudo ethtool -G eth0 rx 1024 tx 1024 2>/dev/null || true
    sudo ethtool -C eth0 rx-usecs 50 2>/dev/null || true
fi

# 6. 创建性能监控脚本
echo ""
echo "6. 创建性能监控脚本..."
cat > monitor_jetson.sh << 'EOF'
#!/bin/bash
# Jetson性能监控脚本

echo "Jetson性能状态监控"
echo "=================="

# 温度
echo "温度状态:"
for thermal in /sys/devices/virtual/thermal/thermal_zone*/temp; do
    if [ -f "$thermal" ]; then
        temp=$(cat $thermal)
        zone=$(basename $(dirname $thermal))
        temp_c=$((temp / 1000))
        echo "  $zone: ${temp_c}°C"
    fi
done

# 电源模式
echo ""
echo "电源模式:"
nvpmodel -q | grep "NV Power Mode"

# CPU频率
echo ""
echo "CPU频率:"
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq | head -4 | while read freq; do
    freq_mhz=$((freq / 1000))
    echo "  CPU: ${freq_mhz}MHz"
done

# GPU频率
echo ""
echo "GPU频率:"
if [ -f "/sys/kernel/debug/bpmp/debug/clk/nafll_gpu/rate" ]; then
    gpu_freq=$(cat /sys/kernel/debug/bpmp/debug/clk/nafll_gpu/rate)
    gpu_mhz=$((gpu_freq / 1000000))
    echo "  GPU: ${gpu_mhz}MHz"
fi

# 内存使用
echo ""
echo "内存使用:"
free -h | grep -E "Mem|Swap"

echo ""
echo "提示: 使用 'sudo jtop' 获取详细的图形化监控"
EOF

chmod +x monitor_jetson.sh

# 7. 创建相机权限设置
echo ""
echo "7. 设置相机权限..."
sudo usermod -a -G video $USER
sudo usermod -a -G plugdev $USER

# 创建udev规则
sudo tee /etc/udev/rules.d/99-hikvision-camera.rules > /dev/null << EOF
# 海康威视相机权限规则
SUBSYSTEM=="usb", ATTRS{idVendor}=="2bdf", MODE="0666", GROUP="plugdev"
# V4L2设备权限
SUBSYSTEM=="video4linux", GROUP="video", MODE="0664"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger

# 8. 创建SDK环境检查脚本
echo ""
echo "8. 创建SDK环境检查脚本..."
cat > check_sdk.sh << 'EOF'
#!/bin/bash
# 检查海康威视SDK安装状态

echo "检查海康威视SDK状态"
echo "=================="

# 检查SDK目录
SDK_PATHS=("/opt/MVS" "/usr/local/MVS")
SDK_FOUND=false

for path in "${SDK_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "✓ 找到SDK目录: $path"
        SDK_FOUND=true
        SDK_PATH=$path
        
        # 检查aarch64特定文件
        if [ -d "$path/Samples/aarch64" ]; then
            echo "✓ 找到aarch64架构支持"
        else
            echo "✗ 缺少aarch64架构支持"
        fi
        
        # 检查Python模块
        if [ -d "$path/Samples/aarch64/Python/MvImport" ]; then
            echo "✓ 找到Python模块"
        else
            echo "✗ 缺少Python模块"
        fi
        
        # 检查库文件
        if [ -d "$path/lib/aarch64" ]; then
            echo "✓ 找到aarch64库文件"
            echo "  库文件列表:"
            ls -la "$path/lib/aarch64/" | head -5
        else
            echo "✗ 缺少aarch64库文件"
        fi
        
        break
    fi
done

if [ "$SDK_FOUND" = false ]; then
    echo "✗ 未找到海康威视SDK"
    echo ""
    echo "请安装SDK:"
    echo "1. 下载ARM64版本的MVS SDK"
    echo "2. 解压到 /opt/MVS/"
    echo "3. 运行安装脚本"
    echo ""
    echo "下载地址: https://www.hikrobotics.com/cn/machinevision/service/download"
    echo "文件名示例: MVS-*-Linux-aarch64-*.tar.gz"
fi

# 检查环境变量
echo ""
echo "环境变量状态:"
if [ -n "$MVCAM_COMMON_RUNENV" ]; then
    echo "✓ MVCAM_COMMON_RUNENV: $MVCAM_COMMON_RUNENV"
else
    echo "✗ MVCAM_COMMON_RUNENV 未设置"
fi

if echo $LD_LIBRARY_PATH | grep -q "aarch64"; then
    echo "✓ LD_LIBRARY_PATH 包含aarch64路径"
else
    echo "✗ LD_LIBRARY_PATH 缺少aarch64路径"
fi

if echo $PYTHONPATH | grep -q "aarch64"; then
    echo "✓ PYTHONPATH 包含aarch64路径"
else
    echo "✗ PYTHONPATH 缺少aarch64路径"
fi
EOF

chmod +x check_sdk.sh

echo ""
echo "=========================================="
echo "✓ Jetson配置完成！"
echo "=========================================="
echo ""
echo "下一步操作:"
echo "1. 重新登录以使权限生效: logout && login"
echo "2. 安装海康威视SDK (ARM64版本)"
echo "3. 运行SDK检查: ./check_sdk.sh"
echo "4. 运行相机程序: ./start_camera.sh"
echo ""
echo "有用的脚本:"
echo "  ./monitor_jetson.sh  - 监控Jetson性能状态"
echo "  ./check_sdk.sh       - 检查SDK安装状态"
echo "  sudo jtop           - 图形化性能监控"
echo "  sudo tegrastats     - 实时状态监控"
echo ""
echo "性能优化提示:"
echo "  - 确保散热充足（推荐主动散热）"
echo "  - 使用高速存储设备（NVMe SSD）"
echo "  - 监控温度，避免过热降频"
echo "  - 定期清理内存缓存"
echo ""

# 显示当前状态
echo "当前设备状态:"
echo "  电源模式: $(nvpmodel -q | grep 'NV Power Mode' | cut -d: -f2)"
echo "  CPU温度: $(($(cat /sys/class/thermal/thermal_zone0/temp)/1000))°C"
echo "  内存使用: $(free -h | awk '/^Mem:/ {print $3"/"$2}')"
echo ""
echo "安装完成！"