#!/usr/bin/env python3
"""
简化的相机设备检测脚本
用于测试设备名称解码问题的修复
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
    logger.info(f"系统架构: {arch}")
    
    # 检查当前环境变量
    current_env = os.environ.get('MVCAM_COMMON_RUNENV')
    if current_env:
        logger.info(f"环境变量已设置: MVCAM_COMMON_RUNENV={current_env}")
        return True
    
    # 自动检测和设置环境变量
    logger.info("自动检测SDK安装路径...")
    
    sdk_paths = [
        "/opt/MVS",
        "/usr/local/MVS", 
        "/home/user/MVS",
        "./MVS"
    ]
    
    for sdk_path in sdk_paths:
        if os.path.exists(sdk_path):
            logger.info(f"找到SDK路径: {sdk_path}")
            
            # 设置基本环境变量
            os.environ['MVS_SDK_PATH'] = sdk_path
            os.environ['MVCAM_COMMON_RUNENV'] = os.path.join(sdk_path, 'lib')
            
            # 根据架构设置库路径
            if arch == 'aarch64':
                lib_path = f"{sdk_path}/lib/aarch64:{sdk_path}/lib"
                python_path = f"{sdk_path}/Samples/aarch64/Python/MvImport"
                logger.info("设置ARM64架构路径")
            else:
                lib_path = f"{sdk_path}/lib/64:{sdk_path}/lib/32"
                python_path = f"{sdk_path}/Samples/64/Python/MvImport"
                logger.info("设置x86_64架构路径")
            
            # 更新环境变量
            current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
            os.environ['LD_LIBRARY_PATH'] = f"{lib_path}:{current_ld_path}" if current_ld_path else lib_path
            
            current_python_path = os.environ.get('PYTHONPATH', '')
            os.environ['PYTHONPATH'] = f"{python_path}:{current_python_path}" if current_python_path else python_path
            
            return True
    
    logger.error("未找到SDK安装路径")
    return False

def test_device_discovery():
    """测试设备发现功能"""
    
    # 设置SDK环境
    if not setup_sdk_environment():
        logger.error("SDK环境设置失败")
        return False
    
    try:
        # 导入SDK
        from MvCameraControl_class import *
        from ctypes import *
        logger.info("SDK导入成功")
        
        # 枚举设备
        device_list = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, device_list)
        if ret != 0:
            logger.error(f"枚举设备失败, 错误代码: {hex(ret)}")
            return False
        
        if device_list.nDeviceNum == 0:
            logger.warning("未发现设备")
            return True
        
        logger.info(f"发现 {device_list.nDeviceNum} 个设备:")
        
        for i in range(device_list.nDeviceNum):
            try:
                mvcc_dev_info = cast(device_list.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
                
                if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                    logger.info(f"  [{i}] GigE设备")
                    try:
                        # 安全地处理设备名称
                        name_array = mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName
                        if hasattr(name_array, 'value'):
                            device_name = name_array.value.decode('ascii', errors='ignore')
                        else:
                            # 处理c_ubyte数组
                            name_bytes = bytes(name_array)
                            device_name = name_bytes.decode('ascii', errors='ignore').rstrip('\x00')
                        
                        logger.info(f"      名称: {device_name}")
                        
                        # 解析IP地址
                        ip_int = mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp
                        ip = f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
                        logger.info(f"      IP: {ip}")
                        
                    except Exception as e:
                        logger.warning(f"      GigE设备信息解析失败: {e}")
                        
                elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                    logger.info(f"  [{i}] USB设备")
                    try:
                        # 安全地处理设备名称
                        name_array = mvcc_dev_info.SpecialInfo.stUsb3VInfo.chUserDefinedName
                        if hasattr(name_array, 'value'):
                            device_name = name_array.value.decode('ascii', errors='ignore')
                        else:
                            # 处理c_ubyte数组
                            name_bytes = bytes(name_array)
                            device_name = name_bytes.decode('ascii', errors='ignore').rstrip('\x00')
                        
                        logger.info(f"      名称: {device_name}")
                        
                    except Exception as e:
                        logger.warning(f"      USB设备信息解析失败: {e}")
                        
                else:
                    logger.info(f"  [{i}] 未知设备类型: {mvcc_dev_info.nTLayerType}")
                    
            except Exception as e:
                logger.error(f"处理设备 {i} 时出错: {e}")
                
        return True
        
    except ImportError as e:
        logger.error(f"SDK导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"设备发现过程出错: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始设备发现测试...")
    
    if test_device_discovery():
        logger.info("设备发现测试完成")
    else:
        logger.error("设备发现测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()