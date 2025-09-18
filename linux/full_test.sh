#!/bin/bash

# 海康威视相机综合测试和修复脚本

echo "=========================================="
echo "海康威视相机 - 综合测试和修复"
echo "=========================================="

# 检查是否以root权限运行
if [ "$EUID" -eq 0 ]; then
    echo "检测到root权限，将执行完整的权限修复"
    SUDO_PREFIX=""
else
    echo "建议以root权限运行以执行完整修复: sudo $0"
    SUDO_PREFIX="sudo"
fi

echo ""
echo "步骤1: 环境变量测试"
echo "===================="
python3 test_env.py

echo ""
echo "步骤2: 权限检查和修复"
echo "===================="

# 运行权限修复脚本
if [ -f "fix_permissions.sh" ]; then
    if [ "$EUID" -eq 0 ]; then
        ./fix_permissions.sh
    else
        echo "需要root权限执行权限修复"
        echo "运行: sudo ./fix_permissions.sh"
    fi
else
    echo "警告: fix_permissions.sh 不存在"
fi

echo ""
echo "步骤3: 权限测试"
echo "================"
python3 test_permissions.py

echo ""
echo "步骤4: 主程序测试（15秒超时）"
echo "============================="

# 运行主程序进行测试
echo "运行主程序测试..."
timeout 15 python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json 2>&1 | head -20

echo ""
echo "步骤5: 结果分析"
echo "================"

echo "如果看到以下输出，表示相应问题已解决:"
echo "✓ '环境变量已设置: MVCAM_COMMON_RUNENV=' - 环境变量问题已解决"
echo "✓ 'SDK导入成功' - SDK导入问题已解决"
echo "✓ '发现 X 个设备:' - 设备发现问题已解决"
echo "✓ '设备连接成功' 或 '设备打开成功' - 权限问题已解决"

echo ""
echo "如果仍然看到以下错误:"
echo "✗ 'AttributeError: c_ubyte_Array_64' - 设备名称解码问题"
echo "✗ 'TypeError: NoneType and str' - 环境变量问题"
echo "✗ '创建设备句柄失败，错误码：80000004' - 权限问题"

echo ""
echo "权限问题的其他解决方案:"
echo "========================"
echo "1. 重新插拔相机设备"
echo "2. 重新启动系统"
echo "3. 检查相机是否被其他程序占用"
echo "4. 使用sudo权限运行:"
echo "   sudo python3 hikvision_camera_controller_linux.py"

echo ""
echo "综合测试完成！"