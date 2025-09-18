#!/bin/bash

# CALLORDER错误修复验证脚本

echo "============================================"
echo "CALLORDER错误修复验证"
echo "============================================"

echo "步骤1: 停止可能冲突的进程"
sudo pkill -f "camera" 2>/dev/null || true
sudo pkill -f "mvs" 2>/dev/null || true
echo "✓ 进程清理完成"

echo ""
echo "步骤2: 等待设备稳定"
sleep 2

echo ""
echo "步骤3: 测试修复后的程序"
echo "运行程序（30秒超时）..."

# 使用timeout运行程序，避免挂起
timeout 30 sudo python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json 2>&1 | tee test_output.log

echo ""
echo "步骤4: 分析结果"
echo "============================================"

# 检查关键输出
if grep -q "相机SDK实例创建成功" test_output.log; then
    echo "✅ SDK实例创建: 成功"
else
    echo "❌ SDK实例创建: 失败"
fi

if grep -q "发现.*个设备" test_output.log; then
    echo "✅ 设备发现: 成功"
else
    echo "❌ 设备发现: 失败"
fi

if grep -q "0x80000004.*CALLORDER" test_output.log; then
    echo "❌ CALLORDER错误: 仍然存在"
    echo ""
    echo "进一步解决方案:"
    echo "1. 重新插拔相机USB线"
    echo "2. 重启系统"
    echo "3. 检查其他程序是否在使用相机"
    echo "4. 验证SDK版本和系统架构匹配"
elif grep -q "设备连接成功\|设备打开成功\|设备句柄创建成功" test_output.log; then
    echo "✅ 设备连接: 成功"
    echo "🎉 CALLORDER错误已解决！"
else
    echo "⚠️  设备连接状态未知"
fi

if grep -q "创建设备句柄失败" test_output.log; then
    echo "❌ 设备句柄创建: 失败"
    ERROR_CODE=$(grep "创建设备句柄失败" test_output.log | grep -o "0x[0-9a-fA-F]*" | head -1)
    if [ ! -z "$ERROR_CODE" ]; then
        echo "错误码: $ERROR_CODE"
        case $ERROR_CODE in
            "0x80000004")
                echo "建议: 函数调用顺序错误，尝试重新插拔设备"
                ;;
            "0x80000011")
                echo "建议: 权限问题，运行 sudo ./fix_permissions.sh"
                ;;
            *)
                echo "建议: 查看完整错误信息分析问题"
                ;;
        esac
    fi
else
    echo "✅ 设备句柄创建: 成功"
fi

echo ""
echo "步骤5: 清理临时文件"
rm -f test_output.log

echo ""
echo "验证完成！"
echo "============================================"

if grep -q "0x80000004.*CALLORDER" test_output.log 2>/dev/null; then
    echo "如果CALLORDER错误仍然存在，请尝试:"
    echo "1. sudo reboot  # 重启系统"
    echo "2. 检查是否有其他相机软件在运行"
    echo "3. 更换USB端口"
    echo "4. 联系技术支持"
else
    echo "如果程序运行正常，现在可以使用完整功能:"
    echo "sudo python3 hikvision_camera_controller_linux.py --help"
fi