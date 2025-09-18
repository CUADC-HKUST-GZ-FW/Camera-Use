#!/usr/bin/env python3
"""
CALLORDER错误专项修复工具
专门解决MV_E_CALLORDER (0x80000004) 错误
"""

import os
import sys
import platform
import logging
import time

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

def fix_callorder_error():
    """修复CALLORDER错误的专项解决方案"""
    logger.info("=" * 60)
    logger.info("CALLORDER错误专项修复")
    logger.info("=" * 60)
    
    if not setup_sdk_environment():
        return False
    
    try:
        # 方法1: 使用全局函数清理SDK状态
        logger.info("方法1: 清理SDK全局状态...")
        
        # 导入SDK
        sys.path.insert(0, os.environ.get('PYTHONPATH', '').split(':')[0])
        from MvCameraControl_class import *
        logger.info("✓ SDK导入成功")
        
        # 尝试清理任何残留状态
        try:
            # 调用全局清理函数（如果存在）
            if hasattr(MvCamera, 'MV_CC_Finalize'):
                ret = MvCamera.MV_CC_Finalize()
                logger.info(f"全局清理结果: {hex(ret)}")
        except:
            pass
        
        # 等待一下让系统稳定
        time.sleep(1)
        
        # 方法2: 重新初始化SDK
        logger.info("方法2: 重新初始化SDK...")
        
        try:
            if hasattr(MvCamera, 'MV_CC_Initialize'):
                ret = MvCamera.MV_CC_Initialize()
                logger.info(f"SDK初始化结果: {hex(ret)}")
        except:
            pass
        
        # 方法3: 单步测试每个SDK调用
        logger.info("方法3: 单步测试SDK调用...")
        
        # 步骤1: 枚举设备
        logger.info("步骤1: 枚举设备...")
        device_list = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, device_list)
        if ret != 0:
            logger.error(f"✗ 枚举设备失败: {hex(ret)}")
            return False
        
        logger.info(f"✓ 枚举设备成功，发现 {device_list.nDeviceNum} 个设备")
        
        if device_list.nDeviceNum == 0:
            logger.warning("未发现设备")
            return True
        
        # 等待设备稳定
        time.sleep(0.5)
        
        # 步骤2: 尝试不同的相机创建方法
        logger.info("步骤2: 尝试创建相机实例...")
        
        # 方法A: 延迟创建
        logger.info("方法A: 延迟创建相机实例...")
        time.sleep(1)
        cam = MvCamera()
        logger.info("✓ 相机实例创建成功")
        
        # 等待实例稳定
        time.sleep(0.5)
        
        # 方法B: 检查设备状态
        logger.info("方法B: 检查设备状态...")
        device_index = 0
        
        try:
            # 获取设备信息指针
            device_info = device_list.pDeviceInfo[device_index]
            logger.info(f"✓ 设备信息指针获取成功: {device_info}")
            
            # 检查设备信息内容
            mvcc_dev_info = cast(device_info, POINTER(MV_CC_DEVICE_INFO)).contents
            logger.info(f"✓ 设备信息解析成功，设备类型: {mvcc_dev_info.nTLayerType}")
            
        except Exception as e:
            logger.error(f"✗ 设备信息检查失败: {e}")
            return False
        
        # 方法C: 逐步尝试创建句柄
        logger.info("方法C: 尝试创建设备句柄...")
        
        # 尝试1: 直接创建
        logger.info("尝试1: 直接创建句柄...")
        ret = cam.MV_CC_CreateHandle(device_list.pDeviceInfo[device_index])
        
        if ret == 0:
            logger.info("✓ 设备句柄创建成功！")
            
            # 继续测试打开设备
            logger.info("测试打开设备...")
            ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret == 0:
                logger.info("✓ 设备打开成功！")
                
                # 获取设备信息
                try:
                    stParam = MVCC_STRINGVALUE()
                    memset(byref(stParam), 0, sizeof(MVCC_STRINGVALUE))
                    ret = cam.MV_CC_GetStringValue("DeviceModelName", stParam)
                    if ret == 0:
                        device_model = stParam.chCurValue.decode('ascii', 'ignore')
                        logger.info(f"✓ 设备型号: {device_model}")
                except Exception as e:
                    logger.warning(f"获取设备信息失败: {e}")
                
                # 正确关闭
                cam.MV_CC_CloseDevice()
                logger.info("✓ 设备已关闭")
            else:
                logger.error(f"✗ 打开设备失败: {hex(ret)}")
            
            # 销毁句柄
            cam.MV_CC_DestroyHandle()
            logger.info("✓ 句柄已销毁")
            
            return True
            
        else:
            logger.error(f"✗ 创建句柄失败: {hex(ret)}")
            
            # 尝试2: 等待后重试
            logger.info("尝试2: 等待2秒后重试...")
            time.sleep(2)
            
            # 创建新的相机实例
            cam2 = MvCamera()
            ret = cam2.MV_CC_CreateHandle(device_list.pDeviceInfo[device_index])
            
            if ret == 0:
                logger.info("✓ 延迟重试成功！")
                cam2.MV_CC_DestroyHandle()
                return True
            else:
                logger.error(f"✗ 延迟重试失败: {hex(ret)}")
                
                # 尝试3: 重新枚举设备
                logger.info("尝试3: 重新枚举设备...")
                
                device_list2 = MV_CC_DEVICE_INFO_LIST()
                ret = MvCamera.MV_CC_EnumDevices(tlayerType, device_list2)
                
                if ret == 0 and device_list2.nDeviceNum > 0:
                    logger.info("✓ 重新枚举成功")
                    
                    cam3 = MvCamera()
                    ret = cam3.MV_CC_CreateHandle(device_list2.pDeviceInfo[0])
                    
                    if ret == 0:
                        logger.info("✓ 重新枚举后创建句柄成功！")
                        cam3.MV_CC_DestroyHandle()
                        return True
                    else:
                        logger.error(f"✗ 重新枚举后仍失败: {hex(ret)}")
                else:
                    logger.error("✗ 重新枚举失败")
        
        return False
        
    except ImportError as e:
        logger.error(f"✗ SDK导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ 修复过程失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("CALLORDER错误专项修复工具")
    
    if fix_callorder_error():
        logger.info("✅ CALLORDER错误修复成功！")
        logger.info("现在可以尝试运行主程序:")
        logger.info("sudo python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json")
    else:
        logger.error("❌ CALLORDER错误修复失败")
        logger.error("建议尝试以下方案:")
        logger.error("1. 重新插拔相机USB线")
        logger.error("2. 重启系统")
        logger.error("3. 检查是否有其他程序在使用相机")
        logger.error("4. 重新安装SDK")

if __name__ == "__main__":
    main()