# 海康威视相机控制程序

基于相机校准文件的海康威视工业相机控制程序，支持图像获取、视频录制和连续拍照功能，提供Windows和Linux两个版本。

## 项目结构

```
Camera_GetData/
├── calibration/                    # 校准文件目录
│   └── 20250910_232046/
│       ├── calibration_result.json # JSON格式校准参数
│       ├── camera_parameters.xml   # XML格式校准参数
│       ├── report.txt              # 校准报告
│       └── undistorted_samples/    # 去畸变样本图像
├── windows/                        # Windows版本
│   └── hikvision_camera_controller.py # 主程序（GUI版本）
├── linux/                         # Linux版本 (Jetson Orin Nano优化)
│   ├── hikvision_camera_controller_linux.py # 主程序（命令行版本）
│   ├── 使用指南.md                  # 详细使用指南
│   ├── CALLORDER错误解决方案.md     # 故障排除指南
│   ├── test_env.py                # 环境变量测试
│   ├── test_permissions.py        # 权限测试
│   ├── fix_permissions.sh         # 权限修复脚本
│   ├── diagnose_camera.sh         # 全面诊断脚本
│   ├── quick_test.sh             # 快速测试脚本
│   ├── verify_fix.sh             # 验证修复脚本
│   ├── jetson_setup.sh           # Jetson优化脚本
│   └── start_camera.sh           # 启动脚本
└── README.md                      # 项目说明（本文件）
```

## 功能特性

### 核心功能
- **单张拍照**: 支持多种图像格式 (JPG, PNG, BMP, TIFF)
- **视频录制**: 支持多种编码格式 (XVID, MJPG, H264, mp4v)
- **连续拍照**: 可设定间隔时间、最大数量和保存格式
- **校准支持**: 自动加载校准参数并进行图像去畸变处理

### 平台差异

| 功能 | Windows版本 | Linux版本 |
|------|-------------|-----------|
| 图形界面 | ✓ (实时预览) | ✗ (命令行) |
| 交互模式 | ✓ | ✓ |
| 批处理模式 | ✓ | ✓ |
| 校准支持 | ✓ | ✓ |
| 后台运行 | ✓ | ✓ |
| 服务化部署 | ✓ | ✓ |

## 快速开始

### Windows版本

1. **安装依赖**:
   ```cmd
   cd windows
   install.bat
   ```

2. **启动程序**:
   ```cmd
   # 从根目录启动
   start_windows.bat
   
   # 或从windows目录启动
   cd windows
   start_camera.bat
   ```

3. **使用示例**:
   ```cmd
   # 拍照模式
   start_windows.bat --capture photo.jpg
   
   # 录像模式
   start_windows.bat --record video.avi --fps 30
   ```

### Linux版本

1. **安装依赖**:
   ```bash
   cd linux
   chmod +x *.sh
   ```

2. **快速测试**:
   ```bash
   # 运行快速测试验证环境
   sudo ./quick_test.sh
   ```

3. **启动程序**:
   ```bash
   # 如果测试通过，运行完整程序
   sudo python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json
   ```

4. **故障排除**:
   ```bash
   # 如果遇到CALLORDER错误 (0x80000004)
   # 最快解决方案：重新插拔USB设备
   
   # 详细诊断
   ./diagnose_camera.sh
   
   # 查看详细解决方案
   cat CALLORDER错误解决方案.md
   ```

## 系统要求

### 共同要求
- Python 3.7+
- OpenCV 4.5.0+
- NumPy 1.19.0+
- 海康威视MVS SDK

### Windows特定要求
- Windows 10/11 x64
- Visual Studio 2019+ 运行时库
- 至少2GB内存

### Linux特定要求
- Ubuntu 18.04+ / CentOS 7+ 或兼容发行版
- **NVIDIA Jetson设备支持 (aarch64架构)**
  - Jetson Orin Nano/NX (推荐)
  - Jetson Xavier NX/AGX
  - Jetson Nano
- GCC 7.0+
- 至少1GB内存（Jetson推荐8GB）

## 校准文件

程序支持两种校准文件格式，位于 `calibration/20250910_232046/` 目录：

- **calibration_result.json**: JSON格式，包含完整校准信息
- **camera_parameters.xml**: OpenCV XML格式，兼容性更好

程序会自动加载校准文件并应用去畸变处理。

## 配置选项

每个版本都包含 `config.json` 配置文件，可以自定义：

- 相机连接参数
- 图像捕获设置
- 视频录制参数
- 连续拍照选项
- 文件路径配置

## 命令行接口

两个版本都支持完整的命令行参数：

```bash
# 通用参数
--calibration FILE    # 指定校准文件
--device INDEX        # 指定设备索引
--capture [FILE]      # 拍照模式
--record [FILE]       # 录像模式
--continuous [DIR]    # 连续拍照模式
--fps FPS            # 视频帧率
--codec CODEC        # 视频编码
--interval SECONDS   # 拍照间隔
--format FORMAT      # 图片格式
--verbose            # 详细输出
```

## 交互模式

进入交互模式后可以使用以下命令：

```
>>> capture [filename]           # 拍照
>>> record [filename] [fps] [codec] # 录像
>>> stop_record                  # 停止录像
>>> continuous [dir] [interval] [format] [count] # 连续拍照
>>> stop_continuous             # 停止连续拍照
>>> calibration [file]          # 加载校准文件
>>> info                        # 显示相机信息
>>> status                      # 显示状态
>>> help                        # 显示帮助
>>> quit                        # 退出
```

## 故障排除

### Linux平台（Jetson Orin Nano）

#### 1. CALLORDER错误 (0x80000004) - 最常见问题
**症状**: 程序报告"函数调用顺序错误"

**快速解决方案**:
```bash
# 方案1: 重新插拔USB设备（解决70%问题）
# 手动拔出USB线，等待5秒，重新插入

# 方案2: 系统重启（解决90%问题）
sudo reboot

# 方案3: 终止冲突进程
sudo pkill -f camera; sudo pkill -f mvs
```

**详细解决方案**:
```bash
# 查看完整解决指南
cd linux
cat CALLORDER错误解决方案.md
```

#### 2. 权限问题
```bash
cd linux
sudo ./fix_permissions.sh
```

#### 3. 环境变量问题
```bash
cd linux
python3 test_env.py
```

#### 4. 完整诊断
```bash
cd linux
./diagnose_camera.sh
```

### Windows平台

### 常见问题

1. **SDK导入失败**
   - 确认海康威视SDK已正确安装
   - 检查环境变量设置
   - 验证Python路径配置

2. **相机连接失败**
   - 检查相机电源和连接
   - 验证网络配置（GigE相机）
   - 确认USB权限（USB相机）

3. **图像获取超时**
   - 检查相机工作状态
   - 调整超时参数
   - 验证网络带宽

### 日志分析

启用详细日志模式获取更多诊断信息：

```bash
# Linux (Jetson)
sudo python3 hikvision_camera_controller_linux.py --calibration ../calibration/20250910_232046/calibration_result.json 2>&1 | tee error.log

# Windows
python hikvision_camera_controller.py --verbose
```

## 🚨 紧急修复指南

### 对于Linux/Jetson用户

如果遇到任何问题，按以下顺序尝试：

1. **最快解决方案**:
   ```bash
   # 重新插拔USB设备，等待5秒后重试
   ```

2. **最有效解决方案**:
   ```bash
   sudo reboot
   ```

3. **自动诊断修复**:
   ```bash
   cd linux
   sudo ./quick_test.sh
   ```

### 成功运行的标志

程序正常工作时，您应该看到：
```
✅ 环境变量检查通过
✅ 相机SDK实例创建成功
✅ 发现 1 个设备
✅ 设备句柄创建成功
✅ 设备连接成功
✅ 校准参数加载成功
相机控制程序已启动...
```

而不是：
```
❌ 创建设备句柄失败，错误码：0x80000004 - MV_E_CALLORDER
```

## 开发指南

### 环境配置

1. **开发环境**:
   ```bash
   git clone <repository>
   cd Camera_GetData
   ```

2. **Windows开发**:
   ```cmd
   cd windows
   pip install -r requirements.txt
   ```

3. **Linux开发**:
   ```bash
   cd linux
   pip3 install -r requirements.txt
   ```

### 代码结构

- **CameraCalibration**: 校准参数加载和图像去畸变
- **HikvisionCamera**: 相机控制和图像获取
- **CameraController**: 主控制器和用户界面

### 扩展功能

程序采用模块化设计，便于扩展：

- 添加新的图像格式支持
- 集成图像处理算法
- 扩展网络功能
- 增加数据库存储

## 部署指南

### 生产环境部署

1. **Windows服务**:
   ```cmd
   # 使用NSSM创建Windows服务
   nssm install HikvisionCamera
   nssm set HikvisionCamera Application "C:\path\to\start_windows.bat"
   ```

2. **Linux服务**:
   ```bash
   # 创建systemd服务
   sudo cp linux/hikvision-camera.service /etc/systemd/system/
   sudo systemctl enable hikvision-camera
   ```

### Docker部署

每个版本都提供Dockerfile支持容器化部署。

## 许可证

本项目采用MIT许可证，详见各版本目录下的LICENSE文件。

## 技术支持

- **文档**: 查看各版本目录下的README.md
- **问题反馈**: 提交Issue到项目仓库
- **技术讨论**: 联系项目维护者

---

**注意**: 使用本程序需要海康威视MVS SDK支持。SDK的获取和使用需要遵循海康威视的许可协议。
