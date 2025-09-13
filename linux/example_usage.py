#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海康威视相机控制程序 - Linux使用示例
展示如何使用相机控制程序的各种功能
"""

import os
import time
from hikvision_camera_controller_linux import CameraControllerLinux

def main():
    """主函数"""
    print("海康威视相机控制程序 - Linux使用示例")
    print("=" * 50)
    
    # 创建控制器
    controller = CameraControllerLinux()
    
    # 加载校准文件
    calibration_files = [
        "../calibration/20250910_232046/calibration_result.json",
        "../calibration/20250910_232046/camera_parameters.xml"
    ]
    
    for cal_file in calibration_files:
        if os.path.exists(cal_file):
            print(f"加载校准文件: {cal_file}")
            controller.load_calibration(cal_file)
            break
    else:
        print("警告: 未找到校准文件，将不进行图像去畸变")
    
    # 初始化相机
    if not controller.initialize_camera():
        print("错误: 相机初始化失败")
        return False
    
    print("相机初始化成功!")
    
    try:
        # 示例1: 拍摄单张照片
        print("\n1. 拍摄单张照片...")
        controller._handle_capture("example_single_photo.jpg")
        time.sleep(1)
        
        # 示例2: 连续拍照5张
        print("\n2. 连续拍照5张（间隔1秒）...")
        controller._handle_continuous("example_photos", 1.0, "jpg", 5)
        
        # 等待连续拍照完成
        while controller.camera.continuous_capture:
            time.sleep(0.5)
        
        # 示例3: 录制5秒视频
        print("\n3. 录制5秒视频...")
        controller._handle_record("example_video.avi", 30, "XVID")
        time.sleep(5)  # 录制5秒
        controller.camera.stop_video_recording()
        
        print("\n所有示例执行完成!")
        print("生成的文件:")
        print("  - example_single_photo.jpg")
        print("  - example_photos/ (目录)")
        print("  - example_video.avi")
        
    except KeyboardInterrupt:
        print("\n示例被用户中断")
    except Exception as e:
        print(f"\n执行示例时发生错误: {e}")
    finally:
        # 清理资源
        controller.camera.disconnect()
        print("程序退出")

if __name__ == "__main__":
    main()
