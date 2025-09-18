#!/bin/bash

# 快速测试脚本：验证CALLORDER错误修复

echo "=========================================="
echo "海康威视相机 - CALLORDER错误修复测试"
echo "=========================================="

# 检查sudo权限
echo ""
echo "检查权限:"
if [ "$EUID" -eq 0 ]; then
    echo "✅ 当前以sudo运行"
else
    echo "⚠️  当前不是sudo运行，某些测试可能失败"
    echo "建议：sudo ./quick_test.sh"
fi

# 检查进程冲突
echo ""
echo "检查进程冲突:"
CAMERA_PROCESSES=$(ps aux | grep -i camera | grep -v grep | grep -v quick_test | wc -l)
MVS_PROCESSES=$(ps aux | grep -i mvs | grep -v grep | wc -l)

if [ $CAMERA_PROCESSES -gt 0 ] || [ $MVS_PROCESSES -gt 0 ]; then
    echo "⚠️  发现可能的进程冲突:"
    ps aux | grep -E "(camera|mvs)" | grep -v grep | grep -v quick_test
    echo "建议：使用 sudo pkill -f camera; sudo pkill -f mvs 终止冲突进程"
else
    echo "✅ 没有发现进程冲突"
fi

# 检查USB设备
echo ""
echo "检查USB设备:"
USB_DEVICES=$(lsusb | grep -i hikvision | wc -l)
if [ $USB_DEVICES -eq 0 ]; then
    echo "❌ 未发现海康威视设备"
    echo "请检查USB连接"
else
    echo "✅ 发现 $USB_DEVICES 个海康威视设备"
    lsusb | grep -i hikvision
fi

# 检查系统架构
ARCH=$(uname -m)
echo ""
echo "系统架构: $ARCH"

# 检查SDK环境变量
echo ""
echo "检查环境变量:"
echo "MVCAM_COMMON_RUNENV: ${MVCAM_COMMON_RUNENV:-未设置}"
echo "LD_LIBRARY_PATH: ${LD_LIBRARY_PATH:-未设置}"
echo "PYTHONPATH: ${PYTHONPATH:-未设置}"

# 运行CALLORDER专项测试
echo ""
echo "=========================================="
echo "CALLORDER专项测试"
echo "=========================================="

# 创建临时测试脚本
cat > /tmp/callorder_test.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
import time

# 添加SDK路径
sys.path.append('/opt/MVS/Samples/aarch64/Python/MvImport')

try:
    from MvCameraControl_class import *
    print("✅ SDK导入成功")
except Exception as e:
    print(f"❌ SDK导入失败: {e}")
    sys.exit(1)

try:
    # 创建SDK实例（有延迟）
    print("🔄 创建SDK实例...")
    camera = MvCamera()
    time.sleep(0.1)  # 添加延迟避免时序问题
    print("✅ 相机SDK实例创建成功")
    
    # 枚举设备
    print("🔄 枚举设备...")
    device_list = MV_CC_DEVICE_INFO_LIST()
    tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
    
    time.sleep(0.2)
    ret = MvCamera.MV_CC_EnumDevices(tlayerType, device_list)
    
    if ret != 0:
        print(f"❌ 设备枚举失败，错误码：{ret:#x}")
        sys.exit(1)
        
    if device_list.nDeviceNum == 0:
        print("❌ 未发现任何设备")
        sys.exit(1)
        
    print(f"✅ 发现 {device_list.nDeviceNum} 个设备")
    
    # 尝试创建设备句柄（这是CALLORDER错误的常见位置）
    print("🔄 创建设备句柄...")
    device_info = cast(device_list.pDeviceInfo[0], POINTER(MV_CC_DEVICE_INFO)).contents
    
    # 关键：添加更长的延迟
    time.sleep(0.5)
    
    ret = camera.MV_CC_CreateHandle(device_info)
    if ret != 0:
        if ret == 0x80000004:
            print(f"❌ CALLORDER错误 (0x80000004)")
            print("🔧 这通常表示:")
            print("   1. 设备被其他程序占用")
            print("   2. SDK状态不一致")
            print("   3. 需要重新插拔USB设备")
            print("   4. 需要重启系统清除状态")
        else:
            print(f"❌ 设备句柄创建失败，错误码：{ret:#x}")
        sys.exit(1)
    
    print("✅ 设备句柄创建成功！")
    print("🎉 CALLORDER错误已解决！")
    
    # 清理资源
    camera.MV_CC_DestroyHandle()
    print("✅ 资源清理完成")
    
except Exception as e:
    print(f"❌ 程序异常: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

# 运行CALLORDER测试
echo "执行CALLORDER专项测试..."
python3 /tmp/callorder_test.py

CALLORDER_TEST_RESULT=$?

# 清理临时文件
rm -f /tmp/callorder_test.py

echo ""
echo "=========================================="
echo "测试结果分析"
echo "=========================================="

if [ $CALLORDER_TEST_RESULT -eq 0 ]; then
    echo "🎉 CALLORDER错误已解决！"
    echo "✅ 可以正常运行完整程序"
    echo ""
    echo "运行完整程序测试:"
    echo "sudo python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json"
else
    echo "❌ CALLORDER错误仍然存在"
    echo ""
    echo "🔧 推荐解决方案（按优先级）:"
    echo "1. 重新插拔USB设备，等待5秒后重试"
    echo "2. 重启系统（最有效的解决方案）"
    echo "3. 检查是否有其他程序在使用相机"
    echo "4. 尝试不同的USB端口"
    echo ""
    echo "详细解决方案请查看："
    echo "cat CALLORDER错误解决方案.md"
fi