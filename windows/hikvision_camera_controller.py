#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海康威视相机控制程序 - Windows版本
功能：图像获取、录像、校准参数加载
作者：Camera Controller
日期：2025-09-13
"""

import os
import sys
import json
import cv2
import numpy as np
import time
import threading
from datetime import datetime
from pathlib import Path
import argparse

# 海康威视SDK导入
try:
    # 添加海康威视SDK路径
    sdk_path = r"C:\Program Files\MVS\Development\Samples\Python\MvImport"
    if sdk_path not in sys.path:
        sys.path.append(sdk_path)
    
    from MvCameraControl_class import *
    from ctypes import *
except ImportError:
    print("错误：无法导入海康威视SDK，请确保已正确安装MVS SDK")
    sys.exit(1)


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
                raise ValueError("不支持的校准文件格式")
            
            print(f"成功加载校准参数：{calibration_file}")
            print(f"图像尺寸：{self.image_width} x {self.image_height}")
            print(f"重投影误差：{self.reprojection_error:.6f}")
            
        except Exception as e:
            print(f"加载校准参数失败：{e}")
            return False
        
        return True
    
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


class HikvisionCamera:
    """海康威视相机控制类"""
    
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
        self.capture_interval = 1.0  # 默认1秒间隔
        self.capture_count = 0
        
    def discover_devices(self):
        """发现设备"""
        device_list = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, device_list)
        if ret != 0:
            print(f"枚举设备失败，错误码：{ret:x}")
            return False
        
        if device_list.nDeviceNum == 0:
            print("未发现设备")
            return False
        
        print(f"发现 {device_list.nDeviceNum} 个设备:")
        for i in range(device_list.nDeviceNum):
            mvcc_dev_info = cast(device_list.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                print(f"  [{i}] GigE设备: {mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName.decode('ascii')}")
                print(f"      IP: {self._parse_ip(mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp)}")
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print(f"  [{i}] USB设备: {mvcc_dev_info.SpecialInfo.stUsb3VInfo.chUserDefinedName.decode('ascii')}")
        
        self.device_list = device_list
        return True
    
    def _parse_ip(self, ip_int):
        """解析IP地址"""
        return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
    
    def connect(self, device_index=0):
        """连接设备"""
        if not self.device_list or device_index >= self.device_list.nDeviceNum:
            print("无效的设备索引")
            return False
        
        # 创建设备句柄
        ret = self.camera.MV_CC_CreateHandle(self.device_list.pDeviceInfo[device_index])
        if ret != 0:
            print(f"创建设备句柄失败，错误码：{ret:x}")
            return False
        
        # 打开设备
        ret = self.camera.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            print(f"打开设备失败，错误码：{ret:x}")
            return False
        
        # 检测网络最佳包大小（仅GigE相机）
        if self.device_list.pDeviceInfo[device_index].contents.nTLayerType == MV_GIGE_DEVICE:
            nPacketSize = self.camera.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                ret = self.camera.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                if ret != 0:
                    print(f"设置包大小失败，错误码：{ret:x}")
        
        # 设置触发模式为关
        ret = self.camera.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        if ret != 0:
            print(f"设置触发模式失败，错误码：{ret:x}")
        
        print("设备连接成功")
        self.is_connected = True
        return True
    
    def start_grabbing(self):
        """开始取流"""
        if not self.is_connected:
            print("设备未连接")
            return False
        
        ret = self.camera.MV_CC_StartGrabbing()
        if ret != 0:
            print(f"开始取流失败，错误码：{ret:x}")
            return False
        
        self.is_grabbing = True
        print("开始取流")
        return True
    
    def stop_grabbing(self):
        """停止取流"""
        if self.is_grabbing:
            ret = self.camera.MV_CC_StopGrabbing()
            if ret != 0:
                print(f"停止取流失败，错误码：{ret:x}")
                return False
            self.is_grabbing = False
            print("停止取流")
        return True
    
    def capture_image(self, save_path=None, apply_calibration=True):
        """捕获单张图像"""
        if not self.is_grabbing:
            print("设备未开始取流")
            return None
        
        try:
            # 获取图像数据
            stFrameInfo = MV_FRAME_OUT_INFO_EX()
            memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
            
            pData = (c_ubyte * (1920 * 1080 * 3))()
            ret = self.camera.MV_CC_GetOneFrameTimeout(pData, sizeof(pData), stFrameInfo, 1000)
            
            if ret != 0:
                print(f"获取图像失败，错误码：{ret:x}")
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
                    print(f"像素格式转换失败，错误码：{ret:x}")
                    return None
                
                image = np.frombuffer(pConvertData, dtype=np.uint8).reshape((stFrameInfo.nHeight, stFrameInfo.nWidth, 3))
            
            # 应用校准参数进行去畸变
            if apply_calibration and self.calibration:
                image = self.calibration.undistort_image(image)
            
            # 保存图像
            if save_path:
                cv2.imwrite(save_path, image)
                print(f"图像已保存：{save_path}")
            
            return image
            
        except Exception as e:
            print(f"捕获图像时发生错误：{e}")
            return None
    
    def start_video_recording(self, output_path, fps=30, codec='XVID'):
        """开始录像"""
        if self.is_recording:
            print("正在录像中")
            return False
        
        if not self.is_grabbing:
            print("设备未开始取流")
            return False
        
        # 获取一帧图像以确定尺寸
        test_image = self.capture_image(apply_calibration=False)
        if test_image is None:
            print("无法获取图像尺寸")
            return False
        
        height, width = test_image.shape[:2]
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*codec)
        self.video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not self.video_writer.isOpened():
            print("无法创建视频文件")
            return False
        
        self.is_recording = True
        self.stop_event.clear()
        
        # 启动录像线程
        self.record_thread = threading.Thread(target=self._recording_loop)
        self.record_thread.start()
        
        print(f"开始录像：{output_path} (FPS: {fps}, 编码: {codec})")
        return True
    
    def _recording_loop(self):
        """录像循环"""
        while self.is_recording and not self.stop_event.is_set():
            image = self.capture_image(apply_calibration=True)
            if image is not None:
                self.video_writer.write(image)
            else:
                time.sleep(0.01)  # 避免CPU占用过高
    
    def stop_video_recording(self):
        """停止录像"""
        if not self.is_recording:
            print("未在录像")
            return False
        
        self.is_recording = False
        self.stop_event.set()
        
        if self.record_thread:
            self.record_thread.join()
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        print("录像已停止")
        return True
    
    def start_continuous_capture(self, output_dir, interval=1.0, format='jpg'):
        """开始连续拍照"""
        if self.continuous_capture:
            print("正在连续拍照中")
            return False
        
        if not self.is_grabbing:
            print("设备未开始取流")
            return False
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.continuous_capture = True
        self.capture_interval = interval
        self.capture_count = 0
        self.stop_event.clear()
        
        # 启动连续拍照线程
        self.capture_thread = threading.Thread(
            target=self._continuous_capture_loop, 
            args=(output_dir, format)
        )
        self.capture_thread.start()
        
        print(f"开始连续拍照：间隔 {interval}s，格式 {format}")
        return True
    
    def _continuous_capture_loop(self, output_dir, format):
        """连续拍照循环"""
        while self.continuous_capture and not self.stop_event.is_set():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"capture_{timestamp}.{format}"
            filepath = os.path.join(output_dir, filename)
            
            image = self.capture_image(filepath, apply_calibration=True)
            if image is not None:
                self.capture_count += 1
                print(f"拍照 #{self.capture_count}: {filename}")
            
            time.sleep(self.capture_interval)
    
    def stop_continuous_capture(self):
        """停止连续拍照"""
        if not self.continuous_capture:
            print("未在连续拍照")
            return False
        
        self.continuous_capture = False
        self.stop_event.set()
        
        if self.capture_thread:
            self.capture_thread.join()
        
        print(f"连续拍照已停止，共拍摄 {self.capture_count} 张图片")
        return True
    
    def disconnect(self):
        """断开设备连接"""
        self.stop_video_recording()
        self.stop_continuous_capture()
        
        if self.is_grabbing:
            self.stop_grabbing()
        
        if self.is_connected:
            ret = self.camera.MV_CC_CloseDevice()
            if ret != 0:
                print(f"关闭设备失败，错误码：{ret:x}")
            
            ret = self.camera.MV_CC_DestroyHandle()
            if ret != 0:
                print(f"销毁设备句柄失败，错误码：{ret:x}")
            
            self.is_connected = False
            print("设备已断开")


class CameraController:
    """相机控制器主类"""
    
    def __init__(self):
        self.camera = None
        self.calibration = None
        
    def load_calibration(self, calibration_file):
        """加载校准文件"""
        self.calibration = CameraCalibration(calibration_file)
        if self.camera:
            self.camera.calibration = self.calibration
    
    def initialize_camera(self):
        """初始化相机"""
        self.camera = HikvisionCamera(self.calibration)
        
        # 发现设备
        if not self.camera.discover_devices():
            return False
        
        # 连接第一个设备
        if not self.camera.connect(0):
            return False
        
        # 开始取流
        if not self.camera.start_grabbing():
            return False
        
        return True
    
    def run_interactive_mode(self):
        """运行交互模式"""
        print("\n=== 海康威视相机控制程序 ===")
        print("命令列表：")
        print("  capture [filename] - 拍照")
        print("  record [filename] [fps] [codec] - 开始录像")
        print("  stop_record - 停止录像")
        print("  continuous [directory] [interval] [format] - 开始连续拍照")
        print("  stop_continuous - 停止连续拍照")
        print("  calibration [file] - 加载校准文件")
        print("  preview - 预览模式")
        print("  help - 显示帮助")
        print("  quit - 退出程序")
        print("=" * 35)
        
        while True:
            try:
                command = input("\n>>> ").strip().split()
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd == 'quit' or cmd == 'exit':
                    break
                
                elif cmd == 'help':
                    self._show_help()
                
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
                    self._handle_continuous(directory, interval, format)
                
                elif cmd == 'stop_continuous':
                    self.camera.stop_continuous_capture()
                
                elif cmd == 'calibration':
                    if len(command) > 1:
                        self.load_calibration(command[1])
                    else:
                        print("请指定校准文件路径")
                
                elif cmd == 'preview':
                    self._handle_preview()
                
                else:
                    print(f"未知命令: {cmd}，输入 'help' 查看帮助")
                    
            except KeyboardInterrupt:
                print("\n程序被用户中断")
                break
            except Exception as e:
                print(f"执行命令时发生错误: {e}")
        
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
    - codec: 可选，编码格式，默认 XVID
    - 示例: record my_video.avi 25 MJPG
  
  stop_record
    - 停止录制视频
  
  continuous [directory] [interval] [format]
    - 开始连续拍照
    - directory: 可选，保存目录，默认 continuous_capture
    - interval: 可选，拍照间隔（秒），默认 1.0
    - format: 可选，图片格式，默认 jpg
    - 示例: continuous photos 0.5 png
  
  stop_continuous
    - 停止连续拍照
  
  calibration [file]
    - 加载相机校准文件（支持 .json 和 .xml）
    - 示例: calibration camera_parameters.xml
  
  preview
    - 进入实时预览模式（按 'q' 退出）
"""
        print(help_text)
    
    def _handle_capture(self, filename):
        """处理拍照命令"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
        
        image = self.camera.capture_image(filename)
        if image is not None:
            print(f"拍照成功: {filename}")
        else:
            print("拍照失败")
    
    def _handle_record(self, filename, fps, codec):
        """处理录像命令"""
        if self.camera.start_video_recording(filename, fps, codec):
            print(f"录像已开始: {filename}")
            print("输入 'stop_record' 停止录像")
        else:
            print("启动录像失败")
    
    def _handle_continuous(self, directory, interval, format):
        """处理连续拍照命令"""
        if self.camera.start_continuous_capture(directory, interval, format):
            print(f"连续拍照已开始: 目录={directory}, 间隔={interval}s, 格式={format}")
            print("输入 'stop_continuous' 停止连续拍照")
        else:
            print("启动连续拍照失败")
    
    def _handle_preview(self):
        """处理预览命令"""
        print("进入预览模式，按 'q' 键退出...")
        
        while True:
            image = self.camera.capture_image(apply_calibration=True)
            if image is not None:
                # 缩放图像以适应显示
                height, width = image.shape[:2]
                if width > 1280:
                    scale = 1280 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    image = cv2.resize(image, (new_width, new_height))
                
                cv2.imshow('Camera Preview', image)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.1)
        
        cv2.destroyAllWindows()
        print("退出预览模式")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='海康威视相机控制程序')
    parser.add_argument('--calibration', '-c', type=str, 
                       help='校准文件路径 (.json 或 .xml)')
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
    
    args = parser.parse_args()
    
    # 创建控制器
    controller = CameraController()
    
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
                print(f"加载默认校准文件: {cal_file}")
                controller.load_calibration(cal_file)
                break
    
    # 初始化相机
    if not controller.initialize_camera():
        print("相机初始化失败")
        sys.exit(1)
    
    # 根据参数执行操作
    try:
        if args.capture:
            filename = args.capture if args.capture != 'auto' else None
            controller._handle_capture(filename)
        
        elif args.record:
            controller._handle_record(args.record, args.fps, args.codec)
            print("录像进行中，按 Ctrl+C 停止...")
            try:
                while controller.camera.is_recording:
                    time.sleep(1)
            except KeyboardInterrupt:
                controller.camera.stop_video_recording()
        
        elif args.continuous:
            controller._handle_continuous(args.continuous, args.interval, args.format)
            print("连续拍照进行中，按 Ctrl+C 停止...")
            try:
                while controller.camera.continuous_capture:
                    time.sleep(1)
            except KeyboardInterrupt:
                controller.camera.stop_continuous_capture()
        
        else:
            # 交互模式
            controller.run_interactive_mode()
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    finally:
        if controller.camera:
            controller.camera.disconnect()


if __name__ == "__main__":
    main()
