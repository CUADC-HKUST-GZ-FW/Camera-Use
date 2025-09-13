#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海康威视相机控制程序使用示例 - Windows版本
"""

import os
import sys
from hikvision_camera_controller import CameraController

def main():
    """示例程序"""
    print("=== 海康威视相机控制示例 - Windows版本 ===")
    
    # 创建控制器
    controller = CameraController()
    
    # 加载校准文件
    calibration_files = [
        "../calibration/20250910_232046/calibration_result.json",
        "calibration/20250910_232046/calibration_result.json",
        "../calibration/20250910_232046/camera_parameters.xml",
        "calibration/20250910_232046/camera_parameters.xml"
    ]
    
    for cal_file in calibration_files:
        if os.path.exists(cal_file):
            print(f"加载校准文件: {cal_file}")
            controller.load_calibration(cal_file)
            break
    else:
        print("未找到校准文件，将不应用校准参数")
    
    # 初始化相机
    print("正在初始化相机...")
    if not controller.initialize_camera():
        print("相机初始化失败，请检查：")
        print("1. 海康威视SDK是否正确安装")
        print("2. 相机是否已连接")
        print("3. 相机驱动是否正常")
        return
    
    print("相机初始化成功！")
    
    # 进入交互模式
    try:
        controller.run_interactive_mode()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    finally:
        if controller.camera:
            controller.camera.disconnect()

if __name__ == "__main__":
    main()
