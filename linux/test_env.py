#!/usr/bin/env python3
"""
测试SDK环境变量设置的脚本
用于验证MVCAM_COMMON_RUNENV和相关环境变量是否正确设置
"""

import os
import sys
import platform
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_sdk_environment():
    """检查SDK环境变量"""
    logger.info("=" * 50)
    logger.info("海康威视SDK环境变量检查")
    logger.info("=" * 50)
    
    # 基本系统信息
    logger.info(f"系统架构: {platform.machine()}")
    logger.info(f"操作系统: {platform.system()}")
    logger.info(f"Python版本: {sys.version}")
    
    # 检查关键环境变量
    env_vars = [
        'MVCAM_COMMON_RUNENV',
        'LD_LIBRARY_PATH', 
        'PYTHONPATH',
        'MVS_SDK_PATH'
    ]
    
    logger.info("\n环境变量状态:")
    logger.info("-" * 30)
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            logger.info(f"{var}: {value}")
        else:
            logger.warning(f"{var}: 未设置")
    
    return True

def detect_sdk_installation():
    """检测SDK安装情况"""
    logger.info("\nSDK安装检测:")
    logger.info("-" * 30)
    
    arch = platform.machine()
    sdk_paths = [
        "/opt/MVS",
        "/usr/local/MVS", 
        "/home/user/MVS",
        "./MVS"
    ]
    
    found_sdk = False
    for sdk_path in sdk_paths:
        if os.path.exists(sdk_path):
            logger.info(f"找到SDK: {sdk_path}")
            found_sdk = True
            
            # 检查关键文件
            key_files = []
            if arch == 'aarch64':
                key_files = [
                    f"{sdk_path}/lib/aarch64/libMvCameraControl.so",
                    f"{sdk_path}/Samples/aarch64/Python/MvImport/MvCameraControl_class.py"
                ]
            else:
                key_files = [
                    f"{sdk_path}/lib/64/libMvCameraControl.so",
                    f"{sdk_path}/lib/32/libMvCameraControl.so",
                    f"{sdk_path}/Samples/64/Python/MvImport/MvCameraControl_class.py"
                ]
            
            for file_path in key_files:
                if os.path.exists(file_path):
                    logger.info(f"  ✓ 存在: {file_path}")
                else:
                    logger.warning(f"  ✗ 缺失: {file_path}")
        else:
            logger.info(f"未找到: {sdk_path}")
    
    if not found_sdk:
        logger.error("未找到任何SDK安装")
    
    return found_sdk

def test_library_loading():
    """测试库加载"""
    logger.info("\n库加载测试:")
    logger.info("-" * 30)
    
    # 检查MVCAM_COMMON_RUNENV
    mvcam_env = os.environ.get('MVCAM_COMMON_RUNENV')
    if not mvcam_env:
        logger.error("MVCAM_COMMON_RUNENV未设置")
        return False
    
    arch = platform.machine()
    if arch == 'aarch64':
        lib_path = os.path.join(mvcam_env, "aarch64", "libMvCameraControl.so")
    else:
        lib_path = os.path.join(mvcam_env, "64", "libMvCameraControl.so")
    
    logger.info(f"检查库文件: {lib_path}")
    
    if os.path.exists(lib_path):
        logger.info("✓ 库文件存在")
        
        # 尝试加载库
        try:
            import ctypes
            lib = ctypes.CDLL(lib_path)
            logger.info("✓ 库加载成功")
            return True
        except Exception as e:
            logger.error(f"✗ 库加载失败: {e}")
            return False
    else:
        logger.error("✗ 库文件不存在")
        return False

def test_python_module():
    """测试Python模块导入"""
    logger.info("\nPython模块测试:")
    logger.info("-" * 30)
    
    try:
        # 尝试导入MvCameraControl_class
        import MvCameraControl_class
        logger.info("✓ MvCameraControl_class导入成功")
        return True
    except ImportError as e:
        logger.error(f"✗ MvCameraControl_class导入失败: {e}")
        
        # 检查PYTHONPATH中的模块路径
        python_path = os.environ.get('PYTHONPATH', '')
        if python_path:
            for path in python_path.split(':'):
                if path and 'MvImport' in path:
                    logger.info(f"检查路径: {path}")
                    if os.path.exists(path):
                        module_file = os.path.join(path, "MvCameraControl_class.py")
                        if os.path.exists(module_file):
                            logger.info(f"  ✓ 模块文件存在: {module_file}")
                        else:
                            logger.warning(f"  ✗ 模块文件不存在: {module_file}")
                    else:
                        logger.warning(f"  ✗ 路径不存在: {path}")
        
        return False

def main():
    """主函数"""
    logger.info("开始SDK环境测试...")
    
    # 执行各项检查
    check_sdk_environment()
    detect_sdk_installation()
    test_library_loading()
    test_python_module()
    
    logger.info("\n" + "=" * 50)
    logger.info("测试完成")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()