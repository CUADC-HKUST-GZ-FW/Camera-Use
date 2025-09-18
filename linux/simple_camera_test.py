#!/usr/bin/env python3
"""
简化的相机测试脚本
专门用于测试MV_E_CALLORDER错误的解决方案
"""

import os
import sys
import platform
import logging

# 设置环境变量以避免X11相关错误
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['DISPLAY'] = ''

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_sdk_environment():
    """设置SDK环境变量"""
    arch = platform.machine()
    
    sdk_paths = ["/opt/MVS", "/usr/local/MVS", "/home/user/MVS", "./MVS"]
    
    for sdk_path in sdk_paths:
        if os.path.exists(sdk_path):
            logger.info(f"找到SDK路径: {sdk_path}")
            
            os.environ['MVS_SDK_PATH'] = sdk_path
            os.environ['MVCAM_COMMON_RUNENV'] = os.path.join(sdk_path, 'lib')
            
            if arch == 'aarch64':
                lib_path = f"{sdk_path}/lib/aarch64:{sdk_path}/lib"
                python_path = f"{sdk_path}/Samples/aarch64/Python/MvImport"
            else:
                lib_path = f"{sdk_path}/lib/64:{sdk_path}/lib/32"
                python_path = f"{sdk_path}/Samples/64/Python/MvImport"
            
            current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
            os.environ['LD_LIBRARY_PATH'] = f"{lib_path}:{current_ld_path}" if current_ld_path else lib_path
            
            current_python_path = os.environ.get('PYTHONPATH', '')
            os.environ['PYTHONPATH'] = f"{python_path}:{current_python_path}" if current_python_path else python_path
            
            return True
    
    logger.error("未找到SDK安装路径")
    return False

def test_correct_sdk_usage():
    """测试正确的SDK使用顺序"""
    logger.info("测试正确的SDK调用顺序...")
    
    if not setup_sdk_environment():
        return False
    
    try:
        # 导入SDK
        sys.path.insert(0, os.environ.get('PYTHONPATH', '').split(':')[0])
        from MvCameraControl_class import *
        logger.info("✓ SDK导入成功")
        
        # 步骤1: 枚举设备（全局函数，不需要MvCamera实例）
        logger.info("步骤1: 枚举设备...")
        device_list = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, device_list)
        if ret != 0:
            logger.error(f"✗ 枚举设备失败: {hex(ret)}")
            return False
        
        if device_list.nDeviceNum == 0:
            logger.warning("未发现设备")
            return True
        
        logger.info(f"✓ 发现 {device_list.nDeviceNum} 个设备")
        
        # 步骤2: 创建相机实例
        logger.info("步骤2: 创建相机实例...")
        cam = MvCamera()
        logger.info("✓ 相机实例创建成功")
        
        # 步骤3: 创建设备句柄
        logger.info("步骤3: 创建设备句柄...")
        device_index = 0
        ret = cam.MV_CC_CreateHandle(device_list.pDeviceInfo[device_index])
        if ret != 0:
            error_msg = get_error_message(ret)
            logger.error(f"✗ 创建设备句柄失败: {hex(ret)} - {error_msg}")
            
            # 特殊处理CALLORDER错误
            if ret == 0x80000004:
                logger.error("函数调用顺序错误的可能原因:")
                logger.error("1. 设备已被其他程序占用")
                logger.error("2. 存在未正确释放的句柄")
                logger.error("3. SDK状态不一致")
                logger.error("解决方案:")
                logger.error("- 重新插拔相机设备")
                logger.error("- 重启程序")
                logger.error("- 检查是否有其他程序在使用相机")
            
            return False
        
        logger.info("✓ 设备句柄创建成功")
        
        # 步骤4: 打开设备
        logger.info("步骤4: 打开设备...")
        ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            error_msg = get_error_message(ret)
            logger.error(f"✗ 打开设备失败: {hex(ret)} - {error_msg}")
            
            # 清理句柄
            cam.MV_CC_DestroyHandle()
            return False
        
        logger.info("✓ 设备打开成功")
        
        # 步骤5: 获取设备基本信息
        logger.info("步骤5: 获取设备信息...")
        try:
            # 获取设备型号
            stParam = MVCC_STRINGVALUE()
            memset(byref(stParam), 0, sizeof(MVCC_STRINGVALUE))
            ret = cam.MV_CC_GetStringValue("DeviceModelName", stParam)
            if ret == 0:
                device_model = stParam.chCurValue.decode('ascii', 'ignore')
                logger.info(f"设备型号: {device_model}")
            
            # 获取序列号
            ret = cam.MV_CC_GetStringValue("DeviceSerialNumber", stParam)
            if ret == 0:
                serial_number = stParam.chCurValue.decode('ascii', 'ignore')
                logger.info(f"设备序列号: {serial_number}")
                
        except Exception as e:
            logger.warning(f"获取设备信息失败: {e}")
        
        # 步骤6: 正确清理资源
        logger.info("步骤6: 清理资源...")
        
        # 关闭设备
        ret = cam.MV_CC_CloseDevice()
        if ret != 0:
            logger.warning(f"关闭设备失败: {hex(ret)}")
        else:
            logger.info("✓ 设备已关闭")
        
        # 销毁句柄
        ret = cam.MV_CC_DestroyHandle()
        if ret != 0:
            logger.warning(f"销毁句柄失败: {hex(ret)}")
        else:
            logger.info("✓ 句柄已销毁")
        
        logger.info("✓ 相机测试完成，所有步骤正确执行")
        return True
        
    except ImportError as e:
        logger.error(f"✗ SDK导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_error_message(error_code):
    """获取错误码对应的消息"""
    error_messages = {
        0x80000001: "MV_E_HANDLE - 错误或无效的句柄",
        0x80000002: "MV_E_SUPPORT - 不支持的功能",
        0x80000003: "MV_E_BUFOVER - 缓存已满",
        0x80000004: "MV_E_CALLORDER - 函数调用顺序错误",
        0x80000005: "MV_E_PARAMETER - 错误的参数",
        0x80000006: "MV_E_RESOURCE - 资源申请失败",
        0x80000007: "MV_E_NODATA - 无数据",
        0x80000008: "MV_E_PRECONDITION - 前置条件有误",
        0x80000009: "MV_E_VERSION - 版本不匹配",
        0x8000000A: "MV_E_NOENOUGH_BUF - 内存空间不足",
        0x8000000B: "MV_E_ABNORMAL_IMAGE - 异常图像",
        0x8000000C: "MV_E_LOAD_LIBRARY - 动态导入DLL失败",
        0x8000000D: "MV_E_NOOUTBUF - 没有可输出的缓存",
        0x8000000E: "MV_E_ENCRYPT - 加密错误",
        0x8000000F: "MV_E_OPENFILE - 打开文件出错",
        0x80000010: "MV_E_UNKNOW - 未知的错误",
        0x80000011: "MV_E_ACCESS_DENIED - 访问被拒绝"
    }
    return error_messages.get(error_code, f"未知错误码: {hex(error_code)}")

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("海康威视相机 - 函数调用顺序测试")
    logger.info("=" * 60)
    
    if test_correct_sdk_usage():
        logger.info("✓ 测试成功完成！")
    else:
        logger.error("✗ 测试失败")
        logger.error("如果遇到CALLORDER错误，请尝试:")
        logger.error("1. 重新插拔相机设备")
        logger.error("2. 检查是否有其他程序在使用相机")
        logger.error("3. 重启系统")

if __name__ == "__main__":
    main()