#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海康威视相机控制程序 - Linux版本
功能：图像获取、录像、校准参数加载（无GUI版本）
作者：Camera Controller
日期：2025-09-13
"""

import os
import sys
import json

# 设置环境变量以避免X11相关错误
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['DISPLAY'] = ''

import cv2
import numpy as np
import time
import threading
from datetime import datetime
from pathlib import Path
import argparse
import signal
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 海康威视SDK导入
SDK_AVAILABLE = False

# 在导入SDK之前检查和设置环境变量
def setup_sdk_environment():
    """设置SDK环境变量"""
    import platform
    
    # 检查当前环境变量
    current_env = os.environ.get('MVCAM_COMMON_RUNENV')
    if current_env:
        logger.info(f"环境变量已设置: MVCAM_COMMON_RUNENV={current_env}")
        return True
    
    # 自动检测和设置环境变量
    logger.info("自动检测SDK安装路径...")
    arch = platform.machine()
    
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
                python_path = f"{sdk_path}/Samples/aarch64/Python"
                logger.info("设置ARM64架构路径")
            else:
                lib_path = f"{sdk_path}/lib/64:{sdk_path}/lib/32"
                python_path = f"{sdk_path}/Samples/64/Python"
                logger.info("设置x86_64架构路径")
            
            # 更新环境变量
            current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
            os.environ['LD_LIBRARY_PATH'] = f"{lib_path}:{current_ld_path}" if current_ld_path else lib_path
            
            current_python_path = os.environ.get('PYTHONPATH', '')
            os.environ['PYTHONPATH'] = f"{python_path}:{current_python_path}" if current_python_path else python_path
            
            logger.info(f"MVCAM_COMMON_RUNENV: {os.environ['MVCAM_COMMON_RUNENV']}")
            logger.info(f"LD_LIBRARY_PATH: {os.environ['LD_LIBRARY_PATH']}")
            logger.info(f"PYTHONPATH: {os.environ['PYTHONPATH']}")
            
            return True
    
    logger.error("未找到SDK安装路径")
    return False

# 设置SDK环境
if not setup_sdk_environment():
    logger.warning("SDK环境变量设置失败，将使用模拟模式")

try:
    # Jetson Orin Nano (aarch64) 下SDK路径
    possible_paths = [
        "/opt/MVS/Samples/aarch64/Python/MvImport",
        "/usr/local/MVS/Samples/aarch64/Python/MvImport", 
        "/opt/MVS/Samples/64/Python/MvImport",  # 通用64位路径
        "/usr/local/MVS/Samples/64/Python/MvImport",
        "/home/user/MVS/Samples/aarch64/Python/MvImport",
        "./MVS/Samples/aarch64/Python/MvImport",
        "./MVS/Samples/64/Python/MvImport"
    ]
    
    sdk_found = False
    for path in possible_paths:
        if os.path.exists(path):
            sys.path.insert(0, path)
            sdk_found = True
            logger.info(f"找到SDK路径: {path}")
            break
    
    if not sdk_found:
        logger.warning("未找到标准SDK路径，尝试使用当前路径")
    
    from MvCameraControl_class import *
    from ctypes import *
    SDK_AVAILABLE = True
    logger.info("海康威视SDK导入成功")
    
except ImportError as e:
    logger.warning("无法导入海康威视SDK，将使用模拟模式进行测试")
    logger.warning(f"错误详情: {e}")
    logger.info("请检查以下路径是否存在SDK文件:")
    for path in ["/opt/MVS/", "/usr/local/MVS/"]:
        logger.info(f"  {path}")
    
    # 创建模拟的SDK类和常量用于测试
    class MockMvCamera:
        def __init__(self):
            pass
            
        def MV_CC_CreateHandle(self, device_info):
            return 0
            
        def MV_CC_OpenDevice(self, access_mode, switch_over_key):
            return 0
            
        def MV_CC_StartGrabbing(self):
            return 0
            
        def MV_CC_StopGrabbing(self):
            return 0
            
        def MV_CC_CloseDevice(self):
            return 0
            
        def MV_CC_DestroyHandle(self):
            return 0
            
        def MV_CC_GetOptimalPacketSize(self):
            return 1500
            
        def MV_CC_SetIntValue(self, key, value):
            return 0
            
        def MV_CC_SetEnumValue(self, key, value):
            return 0
            
        def MV_CC_GetIntValue(self, key):
            return (0, 1920 if 'Width' in key else 1080)
            
        def MV_CC_GetEnumValue(self, key):
            return (0, 17301505)  # Mock pixel format
            
        def MV_CC_GetFloatValue(self, key):
            return (0, 30.0)
            
        def MV_CC_GetOneFrameTimeout(self, data, size, frame_info, timeout):
            # 模拟返回错误，表示无实际相机
            return 0x80000007  # MV_E_TIMEOUT
            
        def MV_CC_ConvertPixelType(self, param):
            return 0
            
        @staticmethod
        def MV_CC_EnumDevices(layer_type, device_list):
            # 模拟没有设备
            device_list.nDeviceNum = 0
            return 0
    
    # 模拟常量
    MvCamera = MockMvCamera
    MV_GIGE_DEVICE = 0x00000001
    MV_USB_DEVICE = 0x00000002
    MV_ACCESS_Exclusive = 1
    MV_TRIGGER_MODE_OFF = 0
    PixelType_Gvsp_Mono8 = 0x01080001
    PixelType_Gvsp_RGB8_Packed = 0x02180014
    PixelType_Gvsp_BGR8_Packed = 0x02180015
    
    # 模拟结构体
    class MockDeviceInfo:
        def __init__(self):
            self.nTLayerType = MV_GIGE_DEVICE
            
    class MockGigEInfo:
        def __init__(self):
            self.chUserDefinedName = b"Mock GigE Camera"
            self.nCurrentIp = 0xC0A80001  # 192.168.0.1
            
    class MockUsb3VInfo:
        def __init__(self):
            self.chUserDefinedName = b"Mock USB Camera"
            
    class MockSpecialInfo:
        def __init__(self):
            self.stGigEInfo = MockGigEInfo()
            self.stUsb3VInfo = MockUsb3VInfo()
            
    class MockMV_CC_DEVICE_INFO:
        def __init__(self):
            self.nTLayerType = MV_GIGE_DEVICE
            self.SpecialInfo = MockSpecialInfo()
            
    class MockMV_CC_DEVICE_INFO_LIST:
        def __init__(self):
            self.nDeviceNum = 0
            self.pDeviceInfo = None
            
    class MockMV_FRAME_OUT_INFO_EX:
        def __init__(self):
            self.nWidth = 1920
            self.nHeight = 1080
            self.enPixelType = PixelType_Gvsp_BGR8_Packed
            self.nFrameLen = 1920 * 1080 * 3
            
    class MockMV_CC_PIXEL_CONVERT_PARAM:
        def __init__(self):
            self.nWidth = 0
            self.nHeight = 0
            self.pSrcData = None
            self.nSrcDataLen = 0
            self.enSrcPixelType = 0
            self.enDstPixelType = 0
            self.pDstBuffer = None
            self.nDstBufferSize = 0
    
    # 模拟ctypes函数
    def cast(obj, type_ptr):
        return MockMV_CC_DEVICE_INFO()
        
    def POINTER(cls):
        return cls
        
    def memset(ptr, value, size):
        pass
        
    def sizeof(obj):
        return 1024
        
    def byref(obj):
        return obj
        
    def c_ubyte(size):
        return type('c_ubyte_array', (), {})()
    
    # 赋值模拟类
    MV_CC_DEVICE_INFO_LIST = MockMV_CC_DEVICE_INFO_LIST
    MV_CC_DEVICE_INFO = MockMV_CC_DEVICE_INFO
    MV_FRAME_OUT_INFO_EX = MockMV_FRAME_OUT_INFO_EX
    MV_CC_PIXEL_CONVERT_PARAM = MockMV_CC_PIXEL_CONVERT_PARAM


class CameraCalibration:
    """相机校准参数类"""
    
    def __init__(self, calibration_file=None):
        self.camera_matrix = None
        self.distortion_coefficients = None
        self.image_width = None
        self.image_height = None
        self.reprojection_error = None
        
        if calibration_file:
            self.load_calibration(calibration_file)
    
    def load_calibration(self, calibration_file):
        """加载校准参数"""
        try:
            if calibration_file.endswith('.json'):
                self._load_from_json(calibration_file)
            elif calibration_file.endswith('.xml'):
                self._load_from_xml(calibration_file)
            else:
                raise ValueError("不支持的校准文件格式，支持 .json 和 .xml")
            
            logger.info(f"成功加载校准参数：{calibration_file}")
            logger.info(f"图像尺寸：{self.image_width} x {self.image_height}")
            logger.info(f"重投影误差：{self.reprojection_error:.6f}")
            return True
            
        except Exception as e:
            logger.error(f"加载校准参数失败：{e}")
            return False
    
    def _load_from_json(self, json_file):
        """从JSON文件加载校准参数"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.camera_matrix = np.array(data['camera_matrix'], dtype=np.float64)
        self.distortion_coefficients = np.array(data['distortion_coefficients'], dtype=np.float64)
        self.image_width = data['calibration_info']['image_size'][0]
        self.image_height = data['calibration_info']['image_size'][1]
        self.reprojection_error = data['reprojection_error']
    
    def _load_from_xml(self, xml_file):
        """从XML文件加载校准参数"""
        fs = cv2.FileStorage(xml_file, cv2.FILE_STORAGE_READ)
        
        self.camera_matrix = fs.getNode('camera_matrix').mat()
        self.distortion_coefficients = fs.getNode('distortion_coefficients').mat()
        self.image_width = int(fs.getNode('image_width').real())
        self.image_height = int(fs.getNode('image_height').real())
        self.reprojection_error = fs.getNode('reprojection_error').real()
        
        fs.release()
    
    def undistort_image(self, image):
        """图像去畸变"""
        if self.camera_matrix is None or self.distortion_coefficients is None:
            return image
        
        return cv2.undistort(image, self.camera_matrix, self.distortion_coefficients)


class HikvisionCameraLinux:
    """海康威视相机控制类 - Linux版本"""
    
    def __init__(self, calibration=None):
        self.camera = MvCamera()
        self.device_list = None
        self.is_connected = False
        self.is_grabbing = False
        self.calibration = calibration
        
        # 录像相关
        self.video_writer = None
        self.is_recording = False
        self.record_thread = None
        self.capture_thread = None
        self.stop_event = threading.Event()
        
        # 连续拍照相关
        self.continuous_capture = False
        self.capture_interval = 1.0
        self.capture_count = 0
        
        # 信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"接收到信号 {signum}，正在安全退出...")
        self.stop_all_operations()
        sys.exit(0)
    
    def discover_devices(self):
        """发现设备"""
        device_list = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, device_list)
        if ret != 0:
            logger.error(f"枚举设备失败，错误码：{ret:x}")
            return False
        
        if device_list.nDeviceNum == 0:
            logger.warning("未发现设备")
            return False
        
        logger.info(f"发现 {device_list.nDeviceNum} 个设备:")
        for i in range(device_list.nDeviceNum):
            mvcc_dev_info = cast(device_list.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                try:
                    # 安全地处理设备名称
                    name_array = mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName
                    if hasattr(name_array, 'value'):
                        device_name = name_array.value.decode('ascii', errors='ignore')
                    else:
                        # 处理c_ubyte数组
                        name_bytes = bytes(name_array)
                        device_name = name_bytes.decode('ascii', errors='ignore').rstrip('\x00')
                    
                    ip = self._parse_ip(mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp)
                    logger.info(f"  [{i}] GigE设备: {device_name}")
                    logger.info(f"      IP: {ip}")
                except Exception as e:
                    logger.warning(f"  [{i}] GigE设备 - 名称解析失败: {e}")
                    ip = self._parse_ip(mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp)
                    logger.info(f"  [{i}] GigE设备: 未知名称")
                    logger.info(f"      IP: {ip}")
                    
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                try:
                    # 安全地处理设备名称
                    name_array = mvcc_dev_info.SpecialInfo.stUsb3VInfo.chUserDefinedName
                    if hasattr(name_array, 'value'):
                        device_name = name_array.value.decode('ascii', errors='ignore')
                    else:
                        # 处理c_ubyte数组
                        name_bytes = bytes(name_array)
                        device_name = name_bytes.decode('ascii', errors='ignore').rstrip('\x00')
                    
                    logger.info(f"  [{i}] USB设备: {device_name}")
                except Exception as e:
                    logger.warning(f"  [{i}] USB设备 - 名称解析失败: {e}")
                    logger.info(f"  [{i}] USB设备: 未知名称")
        
        self.device_list = device_list
        return True
    
    def _parse_ip(self, ip_int):
        """解析IP地址"""
        return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
    
    def _get_error_message(self, error_code):
        """获取错误码对应的消息"""
        error_messages = {
            0x80000001: "MV_E_HANDLE - 错误或无效的句柄",
            0x80000002: "MV_E_SUPPORT - 不支持的功能", 
            0x80000003: "MV_E_BUFOVER - 缓存已满",
            0x80000004: "MV_E_CALLORDER - 函数调用顺序错误",
            0x80000005: "MV_E_PARAMETER - 错误的参数",
            0x80000006: "MV_E_RESOURCE - 资源申请失败",
            0x80000007: "MV_E_NODATA - 无数据",
            0x80000008: "MV_E_PRECONDITION - 前置条件有误，或运行环境已发生变化",
            0x80000009: "MV_E_VERSION - 版本不匹配",
            0x8000000A: "MV_E_NOENOUGH_BUF - 传入的内存空间不足",
            0x8000000B: "MV_E_ABNORMAL_IMAGE - 异常图像，可能是丢包导致图像不完整",
            0x8000000C: "MV_E_LOAD_LIBRARY - 动态导入DLL失败",
            0x8000000D: "MV_E_NOOUTBUF - 没有可输出的缓存",
            0x8000000E: "MV_E_ENCRYPT - 加密错误",
            0x8000000F: "MV_E_OPENFILE - 打开文件出错",
            0x80000010: "MV_E_UNKNOW - 未知的错误",
            0x80000011: "MV_E_ACCESS_DENIED - 访问被拒绝"
        }
        return error_messages.get(error_code, f"未知错误码: {hex(error_code)}")
    
    def connect(self, device_index=0):
        """连接设备"""
        if not self.device_list or device_index >= self.device_list.nDeviceNum:
            logger.error("无效的设备索引")
            return False
        
        # 创建设备句柄
        ret = self.camera.MV_CC_CreateHandle(self.device_list.pDeviceInfo[device_index])
        if ret != 0:
            error_msg = self._get_error_message(ret)
            logger.error(f"创建设备句柄失败，错误码：{hex(ret)} - {error_msg}")
            
            # 提供权限相关的建议
            if ret == 0x80000011:  # MV_E_ACCESS_DENIED
                logger.error("权限被拒绝 - 可能的解决方案:")
                logger.error("1. 运行权限修复脚本: ./fix_permissions.sh")
                logger.error("2. 或者运行: sudo chmod 666 /dev/bus/usb/*/*")
                logger.error("3. 添加用户到plugdev组: sudo usermod -a -G plugdev $USER")
                logger.error("4. 重新插拔相机设备")
                logger.error("5. 或者使用sudo权限运行程序")
            
            return False
        
        # 打开设备
        ret = self.camera.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            logger.error(f"打开设备失败，错误码：{ret:x}")
            return False
        
        # 检测网络最佳包大小（仅GigE相机）
        if self.device_list.pDeviceInfo[device_index].contents.nTLayerType == MV_GIGE_DEVICE:
            nPacketSize = self.camera.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                ret = self.camera.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                if ret != 0:
                    logger.warning(f"设置包大小失败，错误码：{ret:x}")
        
        # 设置触发模式为关
        ret = self.camera.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        if ret != 0:
            logger.warning(f"设置触发模式失败，错误码：{ret:x}")
        
        logger.info("设备连接成功")
        self.is_connected = True
        return True
    
    def start_grabbing(self):
        """开始取流"""
        if not self.is_connected:
            logger.error("设备未连接")
            return False
        
        ret = self.camera.MV_CC_StartGrabbing()
        if ret != 0:
            logger.error(f"开始取流失败，错误码：{ret:x}")
            return False
        
        self.is_grabbing = True
        logger.info("开始取流")
        return True
    
    def stop_grabbing(self):
        """停止取流"""
        if self.is_grabbing:
            ret = self.camera.MV_CC_StopGrabbing()
            if ret != 0:
                logger.error(f"停止取流失败，错误码：{ret:x}")
                return False
            self.is_grabbing = False
            logger.info("停止取流")
        return True
    
    def get_camera_info(self):
        """获取相机信息"""
        if not self.is_connected:
            return None
        
        info = {}
        try:
            # 获取分辨率
            width = self.camera.MV_CC_GetIntValue("Width")[1]
            height = self.camera.MV_CC_GetIntValue("Height")[1]
            info['resolution'] = f"{width}x{height}"
            
            # 获取像素格式
            pixel_format = self.camera.MV_CC_GetEnumValue("PixelFormat")[1]
            info['pixel_format'] = pixel_format
            
            # 获取帧率
            frame_rate = self.camera.MV_CC_GetFloatValue("AcquisitionFrameRate")[1]
            info['frame_rate'] = f"{frame_rate:.2f}"
            
        except Exception as e:
            logger.warning(f"获取相机信息时出错: {e}")
        
        return info
    
    def capture_image(self, save_path=None, apply_calibration=True):
        """捕获单张图像"""
        if not self.is_grabbing:
            logger.error("设备未开始取流")
            return None
        
        try:
            # 获取图像数据
            stFrameInfo = MV_FRAME_OUT_INFO_EX()
            memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
            
            pData = (c_ubyte * (1920 * 1080 * 3))()
            ret = self.camera.MV_CC_GetOneFrameTimeout(pData, sizeof(pData), stFrameInfo, 1000)
            
            if ret != 0:
                logger.error(f"获取图像失败，错误码：{ret:x}")
                return None
            
            # 转换为numpy数组
            image_data = np.frombuffer(pData, dtype=np.uint8, count=stFrameInfo.nFrameLen)
            
            # 根据像素格式转换图像
            if stFrameInfo.enPixelType == PixelType_Gvsp_Mono8:
                image = image_data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif stFrameInfo.enPixelType == PixelType_Gvsp_RGB8_Packed:
                image = image_data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth, 3))
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            elif stFrameInfo.enPixelType == PixelType_Gvsp_BGR8_Packed:
                image = image_data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth, 3))
            else:
                # 其他格式转换为BGR
                nConvertSize = stFrameInfo.nWidth * stFrameInfo.nHeight * 3
                pConvertData = (c_ubyte * nConvertSize)()
                
                stConvertParam = MV_CC_PIXEL_CONVERT_PARAM()
                memset(byref(stConvertParam), 0, sizeof(stConvertParam))
                stConvertParam.nWidth = stFrameInfo.nWidth
                stConvertParam.nHeight = stFrameInfo.nHeight
                stConvertParam.pSrcData = pData
                stConvertParam.nSrcDataLen = stFrameInfo.nFrameLen
                stConvertParam.enSrcPixelType = stFrameInfo.enPixelType
                stConvertParam.enDstPixelType = PixelType_Gvsp_BGR8_Packed
                stConvertParam.pDstBuffer = pConvertData
                stConvertParam.nDstBufferSize = nConvertSize
                
                ret = self.camera.MV_CC_ConvertPixelType(stConvertParam)
                if ret != 0:
                    logger.error(f"像素格式转换失败，错误码：{ret:x}")
                    return None
                
                image = np.frombuffer(pConvertData, dtype=np.uint8).reshape((stFrameInfo.nHeight, stFrameInfo.nWidth, 3))
            
            # 应用校准参数进行去畸变
            if apply_calibration and self.calibration:
                image = self.calibration.undistort_image(image)
            
            # 保存图像
            if save_path:
                # 确保目录存在
                os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
                cv2.imwrite(save_path, image)
                logger.info(f"图像已保存：{save_path}")
            
            return image
            
        except Exception as e:
            logger.error(f"捕获图像时发生错误：{e}")
            return None
    
    def start_video_recording(self, output_path, fps=30, codec='XVID'):
        """开始录像"""
        if self.is_recording:
            logger.warning("正在录像中")
            return False
        
        if not self.is_grabbing:
            logger.error("设备未开始取流")
            return False
        
        # 获取一帧图像以确定尺寸
        test_image = self.capture_image(apply_calibration=False)
        if test_image is None:
            logger.error("无法获取图像尺寸")
            return False
        
        height, width = test_image.shape[:2]
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*codec)
        self.video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not self.video_writer.isOpened():
            logger.error("无法创建视频文件")
            return False
        
        self.is_recording = True
        self.stop_event.clear()
        
        # 启动录像线程
        self.record_thread = threading.Thread(target=self._recording_loop)
        self.record_thread.start()
        
        logger.info(f"开始录像：{output_path} (FPS: {fps}, 编码: {codec})")
        return True
    
    def _recording_loop(self):
        """录像循环"""
        frame_count = 0
        start_time = time.time()
        
        while self.is_recording and not self.stop_event.is_set():
            image = self.capture_image(apply_calibration=True)
            if image is not None:
                self.video_writer.write(image)
                frame_count += 1
                
                # 每100帧输出一次状态
                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    logger.info(f"录像进行中... 帧数: {frame_count}, 实际FPS: {fps:.2f}")
            else:
                time.sleep(0.01)  # 避免CPU占用过高
    
    def stop_video_recording(self):
        """停止录像"""
        if not self.is_recording:
            logger.warning("未在录像")
            return False
        
        self.is_recording = False
        self.stop_event.set()
        
        if self.record_thread:
            self.record_thread.join()
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        logger.info("录像已停止")
        return True
    
    def start_continuous_capture(self, output_dir, interval=1.0, format='jpg', max_count=None):
        """开始连续拍照"""
        if self.continuous_capture:
            logger.warning("正在连续拍照中")
            return False
        
        if not self.is_grabbing:
            logger.error("设备未开始取流")
            return False
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.continuous_capture = True
        self.capture_interval = interval
        self.capture_count = 0
        self.stop_event.clear()
        
        # 启动连续拍照线程
        self.capture_thread = threading.Thread(
            target=self._continuous_capture_loop, 
            args=(output_dir, format, max_count)
        )
        self.capture_thread.start()
        
        logger.info(f"开始连续拍照：间隔 {interval}s，格式 {format}，目录 {output_dir}")
        if max_count:
            logger.info(f"最大拍照数量: {max_count}")
        return True
    
    def _continuous_capture_loop(self, output_dir, format, max_count):
        """连续拍照循环"""
        while self.continuous_capture and not self.stop_event.is_set():
            if max_count and self.capture_count >= max_count:
                logger.info(f"已达到最大拍照数量 {max_count}，停止连续拍照")
                break
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"capture_{timestamp}.{format}"
            filepath = os.path.join(output_dir, filename)
            
            image = self.capture_image(filepath, apply_calibration=True)
            if image is not None:
                self.capture_count += 1
                logger.info(f"拍照 #{self.capture_count}: {filename}")
            
            time.sleep(self.capture_interval)
        
        self.continuous_capture = False
    
    def stop_continuous_capture(self):
        """停止连续拍照"""
        if not self.continuous_capture:
            logger.warning("未在连续拍照")
            return False
        
        self.continuous_capture = False
        self.stop_event.set()
        
        if self.capture_thread:
            self.capture_thread.join()
        
        logger.info(f"连续拍照已停止，共拍摄 {self.capture_count} 张图片")
        return True
    
    def stop_all_operations(self):
        """停止所有操作"""
        self.stop_video_recording()
        self.stop_continuous_capture()
    
    def disconnect(self):
        """断开设备连接"""
        self.stop_all_operations()
        
        if self.is_grabbing:
            self.stop_grabbing()
        
        if self.is_connected:
            ret = self.camera.MV_CC_CloseDevice()
            if ret != 0:
                logger.error(f"关闭设备失败，错误码：{ret:x}")
            
            ret = self.camera.MV_CC_DestroyHandle()
            if ret != 0:
                logger.error(f"销毁设备句柄失败，错误码：{ret:x}")
            
            self.is_connected = False
            logger.info("设备已断开")


class CameraControllerLinux:
    """相机控制器主类 - Linux版本"""
    
    def __init__(self):
        self.camera = None
        self.calibration = None
        
    def load_calibration(self, calibration_file):
        """加载校准文件"""
        self.calibration = CameraCalibration(calibration_file)
        if self.camera:
            self.camera.calibration = self.calibration
    
    def initialize_camera(self, device_index=0):
        """初始化相机"""
        self.camera = HikvisionCameraLinux(self.calibration)
        
        # 发现设备
        if not self.camera.discover_devices():
            return False
        
        # 连接指定设备
        if not self.camera.connect(device_index):
            return False
        
        # 开始取流
        if not self.camera.start_grabbing():
            return False
        
        # 显示相机信息
        info = self.camera.get_camera_info()
        if info:
            logger.info("相机信息:")
            for key, value in info.items():
                logger.info(f"  {key}: {value}")
        
        return True
    
    def run_interactive_mode(self):
        """运行交互模式"""
        print("\n" + "=" * 50)
        print("海康威视相机控制程序 - Linux版本")
        print("=" * 50)
        print("命令列表：")
        print("  capture [filename] - 拍照")
        print("  record [filename] [fps] [codec] - 开始录像")
        print("  stop_record - 停止录像")
        print("  continuous [directory] [interval] [format] [max_count] - 开始连续拍照")
        print("  stop_continuous - 停止连续拍照")
        print("  calibration [file] - 加载校准文件")
        print("  info - 显示相机信息")
        print("  status - 显示当前状态")
        print("  help - 显示帮助")
        print("  quit - 退出程序")
        print("=" * 50)
        
        while True:
            try:
                command = input("\n>>> ").strip().split()
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd in ['quit', 'exit', 'q']:
                    break
                
                elif cmd == 'help':
                    self._show_help()
                
                elif cmd == 'info':
                    self._show_camera_info()
                
                elif cmd == 'status':
                    self._show_status()
                
                elif cmd == 'capture':
                    filename = command[1] if len(command) > 1 else None
                    self._handle_capture(filename)
                
                elif cmd == 'record':
                    filename = command[1] if len(command) > 1 else "video.avi"
                    fps = int(command[2]) if len(command) > 2 else 30
                    codec = command[3] if len(command) > 3 else 'XVID'
                    self._handle_record(filename, fps, codec)
                
                elif cmd == 'stop_record':
                    self.camera.stop_video_recording()
                
                elif cmd == 'continuous':
                    directory = command[1] if len(command) > 1 else "continuous_capture"
                    interval = float(command[2]) if len(command) > 2 else 1.0
                    format = command[3] if len(command) > 3 else 'jpg'
                    max_count = int(command[4]) if len(command) > 4 else None
                    self._handle_continuous(directory, interval, format, max_count)
                
                elif cmd == 'stop_continuous':
                    self.camera.stop_continuous_capture()
                
                elif cmd == 'calibration':
                    if len(command) > 1:
                        self.load_calibration(command[1])
                    else:
                        print("请指定校准文件路径")
                
                else:
                    print(f"未知命令: {cmd}，输入 'help' 查看帮助")
                    
            except KeyboardInterrupt:
                print("\n程序被用户中断")
                break
            except EOFError:
                print("\n程序退出")
                break
            except Exception as e:
                logger.error(f"执行命令时发生错误: {e}")
        
        # 清理资源
        if self.camera:
            self.camera.disconnect()
        
        print("程序退出")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
命令详细说明：
  capture [filename]
    - 拍摄一张照片
    - filename: 可选，指定保存的文件名
    - 示例: capture photo.jpg
  
  record [filename] [fps] [codec]
    - 开始录制视频
    - filename: 可选，默认 video.avi
    - fps: 可选，帧率，默认 30
    - codec: 可选，编码格式，默认 XVID (支持: XVID, MJPG, mp4v)
    - 示例: record my_video.avi 25 MJPG
  
  stop_record
    - 停止录制视频
  
  continuous [directory] [interval] [format] [max_count]
    - 开始连续拍照
    - directory: 可选，保存目录，默认 continuous_capture
    - interval: 可选，拍照间隔（秒），默认 1.0
    - format: 可选，图片格式，默认 jpg
    - max_count: 可选，最大拍照数量，默认无限制
    - 示例: continuous photos 0.5 png 100
  
  stop_continuous
    - 停止连续拍照
  
  calibration [file]
    - 加载相机校准文件（支持 .json 和 .xml）
    - 示例: calibration camera_parameters.xml
  
  info
    - 显示相机详细信息
  
  status
    - 显示当前操作状态

注意事项：
  - Linux版本不支持图形预览功能
  - 录像和连续拍照可以同时进行
  - 使用 Ctrl+C 可以中断当前操作
  - 所有输出文件的目录会自动创建
"""
        print(help_text)
    
    def _show_camera_info(self):
        """显示相机信息"""
        if not self.camera or not self.camera.is_connected:
            print("相机未连接")
            return
        
        info = self.camera.get_camera_info()
        if info:
            print("\n相机信息:")
            print("-" * 30)
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print("无法获取相机信息")
        
        if self.calibration:
            print("\n校准信息:")
            print("-" * 30)
            print(f"  图像尺寸: {self.calibration.image_width}x{self.calibration.image_height}")
            print(f"  重投影误差: {self.calibration.reprojection_error:.6f}")
        else:
            print("\n未加载校准参数")
    
    def _show_status(self):
        """显示当前状态"""
        if not self.camera:
            print("相机未初始化")
            return
        
        print("\n当前状态:")
        print("-" * 30)
        print(f"  连接状态: {'已连接' if self.camera.is_connected else '未连接'}")
        print(f"  取流状态: {'进行中' if self.camera.is_grabbing else '已停止'}")
        print(f"  录像状态: {'进行中' if self.camera.is_recording else '已停止'}")
        print(f"  连续拍照: {'进行中' if self.camera.continuous_capture else '已停止'}")
        if self.camera.continuous_capture:
            print(f"  已拍摄: {self.camera.capture_count} 张")
        print(f"  校准状态: {'已加载' if self.calibration else '未加载'}")
    
    def _handle_capture(self, filename):
        """处理拍照命令"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
        
        # 确保有正确的扩展名
        if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']):
            filename += '.jpg'
        
        image = self.camera.capture_image(filename)
        if image is not None:
            print(f"拍照成功: {filename}")
        else:
            print("拍照失败")
    
    def _handle_record(self, filename, fps, codec):
        """处理录像命令"""
        # 确保有正确的扩展名
        if not any(filename.lower().endswith(ext) for ext in ['.avi', '.mp4', '.mov']):
            filename += '.avi'
        
        if self.camera.start_video_recording(filename, fps, codec):
            print(f"录像已开始: {filename}")
            print("输入 'stop_record' 停止录像")
        else:
            print("启动录像失败")
    
    def _handle_continuous(self, directory, interval, format, max_count):
        """处理连续拍照命令"""
        if self.camera.start_continuous_capture(directory, interval, format, max_count):
            print(f"连续拍照已开始:")
            print(f"  目录: {directory}")
            print(f"  间隔: {interval}s")
            print(f"  格式: {format}")
            if max_count:
                print(f"  最大数量: {max_count}")
            print("输入 'stop_continuous' 停止连续拍照")
        else:
            print("启动连续拍照失败")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='海康威视相机控制程序 - Linux版本')
    parser.add_argument('--calibration', '-c', type=str, 
                       help='校准文件路径 (.json 或 .xml)')
    parser.add_argument('--device', '-d', type=int, default=0,
                       help='设备索引，默认0')
    parser.add_argument('--capture', type=str, nargs='?', const='auto',
                       help='拍照模式，可指定文件名')
    parser.add_argument('--record', type=str, nargs='?', const='video.avi',
                       help='录像模式，可指定文件名')
    parser.add_argument('--fps', type=int, default=30,
                       help='录像帧率，默认30')
    parser.add_argument('--codec', type=str, default='XVID',
                       help='录像编码，默认XVID')
    parser.add_argument('--continuous', type=str, nargs='?', const='continuous_capture',
                       help='连续拍照模式，可指定目录')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='连续拍照间隔（秒），默认1.0')
    parser.add_argument('--format', type=str, default='jpg',
                       help='连续拍照格式，默认jpg')
    parser.add_argument('--max-count', type=int, default=None,
                       help='连续拍照最大数量，默认无限制')
    parser.add_argument('--duration', type=int, default=None,
                       help='录像或连续拍照持续时间（秒），默认无限制')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出模式')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建控制器
    controller = CameraControllerLinux()
    
    # 加载校准文件
    if args.calibration:
        controller.load_calibration(args.calibration)
    else:
        # 尝试加载默认校准文件
        default_calibrations = [
            "../calibration/20250910_232046/calibration_result.json",
            "calibration/20250910_232046/calibration_result.json",
            "../calibration/20250910_232046/camera_parameters.xml",
            "calibration/20250910_232046/camera_parameters.xml"
        ]
        
        for cal_file in default_calibrations:
            if os.path.exists(cal_file):
                logger.info(f"加载默认校准文件: {cal_file}")
                controller.load_calibration(cal_file)
                break
    
    # 初始化相机
    if not controller.initialize_camera(args.device):
        logger.error("相机初始化失败")
        sys.exit(1)
    
    # 根据参数执行操作
    try:
        if args.capture:
            filename = args.capture if args.capture != 'auto' else None
            controller._handle_capture(filename)
        
        elif args.record:
            controller._handle_record(args.record, args.fps, args.codec)
            
            if args.duration:
                logger.info(f"录像将持续 {args.duration} 秒...")
                time.sleep(args.duration)
                controller.camera.stop_video_recording()
            else:
                logger.info("录像进行中，按 Ctrl+C 停止...")
                try:
                    while controller.camera.is_recording:
                        time.sleep(1)
                except KeyboardInterrupt:
                    controller.camera.stop_video_recording()
        
        elif args.continuous:
            controller._handle_continuous(args.continuous, args.interval, args.format, args.max_count)
            
            if args.duration:
                logger.info(f"连续拍照将持续 {args.duration} 秒...")
                time.sleep(args.duration)
                controller.camera.stop_continuous_capture()
            else:
                logger.info("连续拍照进行中，按 Ctrl+C 停止...")
                try:
                    while controller.camera.continuous_capture:
                        time.sleep(1)
                except KeyboardInterrupt:
                    controller.camera.stop_continuous_capture()
        
        else:
            # 交互模式
            controller.run_interactive_mode()
    
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行时发生错误: {e}")
    finally:
        if controller.camera:
            controller.camera.disconnect()


if __name__ == "__main__":
    main()
