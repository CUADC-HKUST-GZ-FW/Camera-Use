#!/bin/bash

# 海康威视相机权限修复脚本

echo "=========================================="
echo "海康威视相机权限修复工具"
echo "=========================================="

# 检查当前用户
echo "当前用户: $(whoami)"
echo "用户组: $(groups)"

# 检查USB设备
echo ""
echo "检查USB设备:"
if command -v lsusb >/dev/null 2>&1; then
    echo "USB设备列表:"
    lsusb | grep -i "2bdf\|hikvision\|MVS" || echo "未找到海康威视设备"
else
    echo "lsusb命令不可用"
fi

# 检查设备节点权限
echo ""
echo "检查设备权限:"
if [ -d "/dev/bus/usb" ]; then
    echo "USB设备目录权限:"
    ls -la /dev/bus/usb/ | head -5
    
    # 查找可能的海康威视设备
    find /dev/bus/usb -name "*" -type f 2>/dev/null | while read device; do
        if [ -r "$device" ]; then
            echo "可读设备: $device"
        else
            echo "不可读设备: $device (需要权限)"
        fi
    done 2>/dev/null | head -10
else
    echo "/dev/bus/usb 目录不存在"
fi

echo ""
echo "推荐的权限修复方法:"
echo "=========================================="

echo "方法1: 添加用户到plugdev组"
echo "sudo usermod -a -G plugdev \$USER"
echo "logout && login  # 重新登录生效"
echo ""

echo "方法2: 创建udev规则文件"
echo "sudo tee /etc/udev/rules.d/99-hikvision-camera.rules << 'EOF'"
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="2bdf", GROUP="plugdev", MODE="0666"'
echo 'EOF'
echo "sudo udevadm control --reload-rules"
echo "sudo udevadm trigger"
echo ""

echo "方法3: 临时修改权限（需要每次重新插拔设备后执行）"
echo "sudo chmod 666 /dev/bus/usb/*/*"
echo ""

echo "方法4: 以root权限运行程序（不推荐，仅测试用）"
echo "sudo python3 hikvision_camera_controller_linux.py"
echo ""

echo "检查Jetson特定设置:"
echo "=========================================="

# 检查Jetson特定的权限设置
if [ -f "/etc/nv_tegra_release" ]; then
    echo "检测到Jetson设备"
    
    # 检查nvidia相关组
    if groups | grep -q nvidia; then
        echo "✓ 用户已在nvidia组"
    else
        echo "✗ 用户不在nvidia组，建议添加:"
        echo "sudo usermod -a -G nvidia \$USER"
    fi
    
    # 检查dialout组（用于串口设备）
    if groups | grep -q dialout; then
        echo "✓ 用户已在dialout组"
    else
        echo "✗ 用户不在dialout组，建议添加:"
        echo "sudo usermod -a -G dialout \$USER"
    fi
    
    # 检查video组
    if groups | grep -q video; then
        echo "✓ 用户已在video组"
    else
        echo "✗ 用户不在video组，建议添加:"
        echo "sudo usermod -a -G video \$USER"
    fi
fi

echo ""
echo "执行建议的修复步骤:"
echo "=========================================="

# 自动执行一些修复
echo "1. 创建udev规则..."
if [ ! -f "/etc/udev/rules.d/99-hikvision-camera.rules" ]; then
    sudo tee /etc/udev/rules.d/99-hikvision-camera.rules > /dev/null << 'EOF'
# 海康威视相机设备权限规则
SUBSYSTEM=="usb", ATTRS{idVendor}=="2bdf", GROUP="plugdev", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="2bdf", ATTRS{idProduct}=="*", GROUP="plugdev", MODE="0666"
EOF
    echo "✓ udev规则已创建"
    
    echo "2. 重新加载udev规则..."
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "✓ udev规则已重新加载"
else
    echo "✓ udev规则文件已存在"
fi

echo ""
echo "3. 添加用户到相关组..."
current_user=$(whoami)

# 添加到plugdev组
if ! groups | grep -q plugdev; then
    sudo usermod -a -G plugdev $current_user
    echo "✓ 已添加用户到plugdev组"
else
    echo "✓ 用户已在plugdev组"
fi

# 如果是Jetson，添加到其他相关组
if [ -f "/etc/nv_tegra_release" ]; then
    for group in nvidia video dialout; do
        if ! groups | grep -q $group; then
            sudo usermod -a -G $group $current_user
            echo "✓ 已添加用户到${group}组"
        else
            echo "✓ 用户已在${group}组"
        fi
    done
fi

echo ""
echo "修复完成！"
echo "=========================================="
echo "请执行以下操作之一:"
echo "1. 重新登录系统（推荐）"
echo "2. 或者重新插拔相机设备"
echo "3. 然后重新运行相机程序"
echo ""
echo "如果问题仍然存在，请尝试:"
echo "sudo python3 hikvision_camera_controller_linux.py"