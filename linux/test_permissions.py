#!/usr/bin/env python3
"""
相机权限测试脚本
专门用于测试和诊断相机设备权限问题
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

# 在模块级别导入SDK（避免在函数内部使用import *）
try:
    from MvCameraControl_class import *
    from ctypes import cast, POINTER, byref, sizeof, memset
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

def test_camera_permissions():
    """测试相机权限"""
    logger.info("开始相机权限测试...")
    
    if not setup_sdk_environment():
        return False
    
    if not SDK_AVAILABLE:
        logger.error("✗ SDK不可用，请检查安装和环境变量")
        return False
    
    try:
        logger.info("✓ SDK导入成功")
        
        # 枚举设备
        device_list = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, device_list)
        if ret != 0:
            logger.error(f"✗ 枚举设备失败, 错误代码: {hex(ret)}")
            return False
        
        if device_list.nDeviceNum == 0:
            logger.warning("! 未发现相机设备")
            return True
        
        logger.info(f"✓ 发现 {device_list.nDeviceNum} 个设备")
        
        # 测试每个设备的权限
        for i in range(device_list.nDeviceNum):
            logger.info(f"测试设备 [{i}]...")
            
            # 创建相机对象
            cam = MvCamera()
            
            # 尝试创建设备句柄
            ret = cam.MV_CC_CreateHandle(device_list.pDeviceInfo[i])
            if ret != 0:
                error_msg = get_error_message(ret)
                logger.error(f"✗ 创建设备句柄失败: {hex(ret)} - {error_msg}")
                
                if ret in [0x80000004, 0x80000011]:  # CALLORDER or ACCESS_DENIED
                    logger.error("可能的解决方案:")
                    logger.error("  1. 运行: sudo ./fix_permissions.sh")
                    logger.error("  2. 或临时解决: sudo chmod 666 /dev/bus/usb/*/*")
                    logger.error("  3. 或以root权限运行: sudo python3 test_permissions.py")
                    logger.error("  4. 检查是否有其他程序在使用相机")
                
                continue
            
            logger.info("✓ 设备句柄创建成功")
            
            # 尝试打开设备
            ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret != 0:
                error_msg = get_error_message(ret)
                logger.error(f"✗ 打开设备失败: {hex(ret)} - {error_msg}")
                
                # 销毁句柄
                cam.MV_CC_DestroyHandle()
                continue
            
            logger.info("✓ 设备打开成功")
            
            # 获取设备信息
            try:
                # 获取设备型号名称
                stParam = MVCC_STRINGVALUE()
                memset(byref(stParam), 0, sizeof(MVCC_STRINGVALUE))
                ret = cam.MV_CC_GetStringValue("DeviceModelName", stParam)
                if ret == 0:
                    device_model = stParam.chCurValue.decode('ascii', 'ignore')
                    logger.info(f"  设备型号: {device_model}")
                
                # 获取序列号
                ret = cam.MV_CC_GetStringValue("DeviceSerialNumber", stParam)
                if ret == 0:
                    serial_number = stParam.chCurValue.decode('ascii', 'ignore')
                    logger.info(f"  序列号: {serial_number}")
                
            except Exception as e:
                logger.warning(f"获取设备信息失败: {e}")
            
            # 关闭设备
            cam.MV_CC_CloseDevice()
            cam.MV_CC_DestroyHandle()
            
            logger.info(f"✓ 设备 [{i}] 权限测试通过")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 权限测试失败: {e}")
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

def check_system_permissions():
    """检查系统权限设置"""
    logger.info("检查系统权限设置...")
    
    import subprocess
    import pwd
    
    # 检查当前用户
    current_user = pwd.getpwuid(os.getuid()).pw_name
    logger.info(f"当前用户: {current_user}")
    
    # 检查用户组
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout.strip()
        logger.info(f"用户组: {groups}")
        
        # 检查关键组
        important_groups = ['plugdev', 'dialout', 'video', 'audio']
        for group in important_groups:
            if group in groups:
                logger.info(f"✓ 用户在 {group} 组")
            else:
                logger.warning(f"✗ 用户不在 {group} 组")
    except Exception as e:
        logger.warning(f"检查用户组失败: {e}")
    
    # 检查USB设备权限
    usb_devices_dir = "/dev/bus/usb"
    if os.path.exists(usb_devices_dir):
        logger.info("检查USB设备权限...")
        try:
            for root, dirs, files in os.walk(usb_devices_dir):
                for file in files:
                    device_path = os.path.join(root, file)
                    if os.access(device_path, os.R_OK | os.W_OK):
                        logger.info(f"✓ 可访问: {device_path}")
                        break  # 只检查第一个可访问的设备
                    else:
                        logger.warning(f"✗ 无权限: {device_path}")
                        break  # 只检查第一个设备
                break  # 只检查第一个目录
        except Exception as e:
            logger.warning(f"检查USB权限失败: {e}")

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("海康威视相机权限测试")
    logger.info("=" * 50)
    
    # 检查系统权限
    check_system_permissions()
    
    logger.info("")
    
    # 测试相机权限
    if test_camera_permissions():
        logger.info("权限测试完成!")
    else:
        logger.error("权限测试失败!")
        logger.error("请运行权限修复脚本: sudo ./fix_permissions.sh")

if __name__ == "__main__":
    main()