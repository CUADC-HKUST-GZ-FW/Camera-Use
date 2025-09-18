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
echo "如果未出现 'c_ubyte_Array_64' object has no attribute 'decode' 错误，"
echo "说明设备名称解码问题已修复。"