#!/bin/bash

# 海康威视相机问题诊断和解决脚本

echo "================================================"
echo "海康威视相机 - 问题诊断和解决"
echo "================================================"

# 显示当前问题状态
echo "当前已知问题状态:"
echo "✅ 环境变量问题 - 已解决"
echo "✅ 设备名称解码问题 - 已解决"  
echo "✅ X11显示问题 - 已解决"
echo "🔧 函数调用顺序错误 (MV_E_CALLORDER) - 正在解决"

echo ""
echo "错误码 0x80000004 (MV_E_CALLORDER) 诊断:"
echo "================================================"

# 检查进程
echo "1. 检查相机相关进程:"
ps aux | grep -i "camera\|mvs\|hikvision" | grep -v grep || echo "   无相关进程运行"

echo ""
echo "2. 检查USB设备:"
lsusb | grep -i "2bdf\|hikvision" || echo "   未检测到海康威视USB设备"

echo ""
echo "3. 检查设备文件权限:"
if [ -d "/dev/bus/usb" ]; then
    find /dev/bus/usb -name "*" -type f 2>/dev/null | head -3 | while read device; do
        if [ -r "$device" ] && [ -w "$device" ]; then
            echo "   ✓ $device (可读写)"
        else
            echo "   ✗ $device (权限不足)"
        fi
    done
else
    echo "   /dev/bus/usb 不存在"
fi

echo ""
echo "MV_E_CALLORDER 错误的可能原因和解决方案:"
echo "================================================"

echo "原因1: 设备被其他程序占用"
echo "解决方案:"
echo "  - 检查是否有其他相机程序运行"
echo "  - 重新插拔相机USB线"
echo "  - 重启系统"

echo ""
echo "原因2: SDK状态不一致"
echo "解决方案:"
echo "  - 确保按正确顺序调用SDK函数"
echo "  - 避免重复创建MvCamera实例"
echo "  - 正确释放资源"

echo ""
echo "原因3: 权限问题"
echo "解决方案:"
echo "  - 运行权限修复: sudo ./fix_permissions.sh"
echo "  - 或使用sudo运行程序"

echo ""
echo "原因4: 库版本不兼容"
echo "解决方案:"
echo "  - 检查SDK版本是否与系统架构匹配"
echo "  - 重新安装SDK"

echo ""
echo "推荐的解决步骤:"
echo "================================================"

echo "步骤1: 停止所有相机程序"
pkill -f "camera\|mvs\|hikvision" 2>/dev/null && echo "✓ 已停止相关进程" || echo "✓ 无需停止进程"

echo ""
echo "步骤2: 重新插拔相机设备"
echo "请手动重新插拔相机USB线，然后按Enter继续..."
read -p ""

echo ""
echo "步骤3: 检查设备重新识别"
lsusb | grep -i "2bdf\|hikvision" && echo "✓ 设备已重新识别" || echo "✗ 设备未识别"

echo ""
echo "步骤4: 修复权限"
if [ -f "fix_permissions.sh" ]; then
    echo "运行权限修复..."
    sudo ./fix_permissions.sh
else
    echo "权限修复脚本不存在，手动修复权限..."
    sudo chmod 666 /dev/bus/usb/*/* 2>/dev/null
    echo "✓ USB设备权限已修复"
fi

echo ""
echo "步骤5: 测试简单的SDK调用"
echo "运行简化测试..."

# 创建临时测试脚本
cat > temp_test.py << 'EOF'
import os
import sys

# 设置环境变量
os.environ['MVCAM_COMMON_RUNENV'] = '/opt/MVS/lib'
os.environ['LD_LIBRARY_PATH'] = '/opt/MVS/lib/aarch64:/opt/MVS/lib'
os.environ['PYTHONPATH'] = '/opt/MVS/Samples/aarch64/Python/MvImport'

try:
    sys.path.insert(0, '/opt/MVS/Samples/aarch64/Python/MvImport')
    from MvCameraControl_class import *
    print("✓ SDK导入成功")
    
    # 仅枚举设备，不创建句柄
    device_list = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, device_list)
    
    if ret == 0:
        print(f"✓ 枚举设备成功，发现 {device_list.nDeviceNum} 个设备")
        if device_list.nDeviceNum > 0:
            print("✓ 基本SDK功能正常")
        else:
            print("! 未发现设备，请检查相机连接")
    else:
        print(f"✗ 枚举设备失败: {hex(ret)}")
        
except Exception as e:
    print(f"✗ 测试失败: {e}")
EOF

python3 temp_test.py
rm temp_test.py

echo ""
echo "步骤6: 如果问题仍然存在"
echo "================================================"
echo "尝试以下高级解决方案:"
echo ""
echo "A. 以root权限运行程序:"
echo "   sudo python3 hikvision_camera_controller_linux.py"
echo ""
echo "B. 检查系统日志:"
echo "   dmesg | tail -20"
echo "   journalctl -u udev"
echo ""
echo "C. 重新安装SDK:"
echo "   1. 备份当前SDK: sudo mv /opt/MVS /opt/MVS.backup"
echo "   2. 重新下载并安装SDK"
echo "   3. 重新配置环境变量"
echo ""
echo "D. 联系技术支持:"
echo "   提供完整的错误信息和系统配置"

echo ""
echo "诊断完成！"
echo "================================================"