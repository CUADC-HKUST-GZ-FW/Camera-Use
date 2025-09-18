#!/bin/bash

# 快速测试脚本：验证设备名称解码修复

echo "=========================================="
echo "海康威视相机 - 设备名称解码修复测试"
echo "=========================================="

# 检查系统架构
ARCH=$(uname -m)
echo "系统架构: $ARCH"

# 检查SDK环境变量
echo ""
echo "检查环境变量:"
echo "MVCAM_COMMON_RUNENV: ${MVCAM_COMMON_RUNENV:-未设置}"
echo "LD_LIBRARY_PATH: ${LD_LIBRARY_PATH:-未设置}"
echo "PYTHONPATH: ${PYTHONPATH:-未设置}"

# 运行环境测试
echo ""
echo "运行环境测试..."
python3 test_env.py

echo ""
echo "运行主程序（仅设备发现）..."
echo "如果看到设备列表而不是AttributeError，说明修复成功"
echo ""

# 运行主程序但立即退出（通过超时）
timeout 10 python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json || true

echo ""
echo "测试完成！"
echo "=========================================="
echo "结果分析:"

if timeout 10 python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json 2>&1 | grep -q "c_ubyte_Array_64.*decode"; then
    echo "✗ 设备名称解码问题仍存在"
else
    echo "✅ 设备名称解码问题已修复"
fi

if timeout 10 python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json 2>&1 | grep -q "SDK导入成功"; then
    echo "✅ SDK导入问题已解决"
else
    echo "✗ SDK导入问题仍存在"
fi

if timeout 10 python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json 2>&1 | grep -q "发现.*个设备"; then
    echo "✅ 设备发现功能正常"
else
    echo "✗ 设备发现功能异常"
fi

if timeout 10 python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json 2>&1 | grep -q "0x80000004.*CALLORDER"; then
    echo "⚠️  检测到函数调用顺序错误 (CALLORDER)"
    echo ""
    echo "CALLORDER错误解决方案:"
    echo "1. 重新插拔相机USB设备"
    echo "2. 检查是否有其他程序在使用相机"
    echo "3. 运行完整诊断: chmod +x diagnose_camera.sh && ./diagnose_camera.sh"
    echo "4. 尝试sudo权限: sudo python3 hikvision_camera_controller_linux.py"
elif timeout 10 python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json 2>&1 | grep -q "设备连接成功\|设备打开成功"; then
    echo "✅ 相机权限和连接正常"
else
    echo "⚠️  相机连接可能存在问题"
fi

echo ""
echo "如果仍有问题，请运行详细诊断:"
echo "chmod +x diagnose_camera.sh && ./diagnose_camera.sh"