# 海康威视相机控制程序 - Linux版本

## 概述

这是海康威视相机控制程序的Linux命令行版本，专为生产环境设计，无需图形界面支持。程序支持图像获取、视频录制、连续拍照等功能，并可加载相机校准参数进行图像去畸变处理。

**特别优化支持NVIDIA Jetson设备（包括Jetson Orin Nano aarch64架构）**

## 功能特性

- **单张拍照**: 支持多种图像格式 (JPG, PNG, BMP等)
- **视频录制**: 支持多种编码格式 (XVID, MJPG, H264等)
- **连续拍照**: 可设定间隔时间和最大数量
- **校准支持**: 自动加载校准参数并进行图像去畸变
- **命令行界面**: 完整的交互式命令行界面
- **后台运行**: 支持后台模式和守护进程
- **信号处理**: 安全的程序退出和资源清理

## 系统要求

### 操作系统
- Ubuntu 18.04+ / Debian 10+
- CentOS 7+ / RHEL 7+ / Rocky Linux 8+
- **NVIDIA Jetson系列 (推荐JetPack 5.0+)**
  - Jetson Orin Nano/NX
  - Jetson Xavier NX/AGX
  - Jetson Nano (较老设备，性能受限)
- 其他支持Python 3.7+的Linux发行版

### 硬件要求
- **通用设备**:
  - CPU: x64或ARM64架构
  - 内存: 至少1GB可用内存
  - 存储: 至少1GB可用空间
- **Jetson设备**:
  - 推荐8GB内存版本（Orin Nano 8GB）
  - 高速microSD卡或NVMe SSD
  - 充足的散热（主动散热风扇推荐）
  - 稳定电源供应（推荐官方电源适配器）
- 网络: 千兆网卡（用于GigE相机）
- USB: USB 3.0接口（用于USB相机）

### 软件依赖
- Python 3.7+
- OpenCV 4.5.0+
- NumPy 1.19.0+
- 海康威视MVS SDK (Linux版本)

## 安装指南

### 自动安装

运行安装脚本进行一键安装：

```bash
chmod +x install.sh
./install.sh
```

安装脚本会自动：
1. 检测操作系统类型
2. 安装系统依赖包
3. 安装Python依赖
4. 检查SDK安装状态
5. 设置相机权限
6. 创建启动脚本

### 手动安装

#### 1. 安装系统依赖

**Ubuntu/Debian (包括Jetson):**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-dev
sudo apt-get install build-essential cmake
sudo apt-get install libusb-1.0-0-dev

# Jetson设备通常预装OpenCV，检查是否存在
python3 -c "import cv2; print('OpenCV version:', cv2.__version__)" || {
    sudo apt-get install python3-opencv
}

# Jetson特定依赖
if [ -f "/etc/nv_tegra_release" ]; then
    sudo apt-get install nvidia-l4t-camera
    sudo apt-get install v4l-utils
fi
```

**CentOS/RHEL:**
```bash
sudo yum update
sudo yum install python3 python3-pip python3-devel
sudo yum install opencv-devel python3-opencv
sudo yum install gcc gcc-c++ make cmake
sudo yum install libusb-devel
```

#### 2. 安装Python依赖

```bash
pip3 install -r requirements.txt
```

#### 3. 安装海康威视SDK

**重要：Jetson设备需要ARM64版本的SDK**

1. 从[海康威视官网](https://www.hikrobotics.com/cn/machinevision/service/download)下载对应架构的Linux版本MVS SDK
   - **Jetson (aarch64)**: 下载 `MVS-*-Linux-aarch64-*.tar.gz`
   - **普通PC (x86_64)**: 下载 `MVS-*-Linux-x86_64-*.tar.gz`

2. 解压SDK到系统路径：
   ```bash
   # 以aarch64版本为例
   sudo tar -xzf MVS-*-Linux-aarch64-*.tar.gz -C /opt/
   sudo mv /opt/MVS* /opt/MVS
   ```

3. 安装SDK：
   ```bash
   cd /opt/MVS
   sudo ./install.sh
   ```

#### 4. 设置环境变量

```bash
# 添加到 ~/.bashrc 或 ~/.profile
export MVS_SDK_PATH="/opt/MVS"
export MVCAM_COMMON_RUNENV="$MVS_SDK_PATH/lib"

# 根据架构设置库路径
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    # Jetson/ARM64设备
    export LD_LIBRARY_PATH="$MVS_SDK_PATH/lib/aarch64:$MVS_SDK_PATH/lib:$LD_LIBRARY_PATH"
    export PYTHONPATH="$MVS_SDK_PATH/Samples/aarch64/Python:$PYTHONPATH"
else
    # x86_64设备
    export LD_LIBRARY_PATH="$MVS_SDK_PATH/lib/64:$MVS_SDK_PATH/lib/32:$LD_LIBRARY_PATH"
    export PYTHONPATH="$MVS_SDK_PATH/Samples/64/Python:$PYTHONPATH"
fi
```

或使用提供的环境变量脚本：
```bash
source setup_env.sh
```

#### 5. 设置USB权限（仅USB相机需要）

```bash
# 创建udev规则
sudo tee /etc/udev/rules.d/99-mvs-camera.rules << EOF
SUBSYSTEM=="usb", ATTRS{idVendor}=="2bdf", MODE="0666", GROUP="plugdev"
EOF

# 重新加载规则
sudo udevadm control --reload-rules
sudo udevadm trigger

# 将用户添加到plugdev组
sudo usermod -a -G plugdev $USER
```

## 使用方法

### 快速启动

```bash
# 使用启动脚本（推荐）
./start_camera.sh

# 或直接运行Python程序
python3 hikvision_camera_controller_linux.py
```

### 命令行选项

```bash
python3 hikvision_camera_controller_linux.py [选项]

选项:
  --calibration, -c FILE    指定校准文件路径
  --device, -d INDEX        指定设备索引（默认0）
  --capture [FILE]          拍照模式，可指定文件名
  --record [FILE]           录像模式，可指定文件名
  --fps FPS                 录像帧率（默认30）
  --codec CODEC             录像编码（默认XVID）
  --continuous [DIR]        连续拍照模式，可指定目录
  --interval SECONDS        连续拍照间隔（默认1.0秒）
  --format FORMAT           图片格式（默认jpg）
  --max-count COUNT         连续拍照最大数量
  --duration SECONDS        操作持续时间（秒）
  --verbose, -v             详细输出模式
  --help, -h                显示帮助信息
```

### 使用示例

#### 1. 交互模式

```bash
./start_camera.sh
```

进入交互模式后，可以使用以下命令：

```
>>> capture photo.jpg          # 拍照
>>> record video.avi 25 MJPG   # 录像
>>> continuous photos 0.5 png 100  # 连续拍照
>>> calibration camera_parameters.xml  # 加载校准
>>> info                       # 显示相机信息
>>> status                     # 显示状态
>>> help                       # 显示帮助
>>> quit                       # 退出
```

#### 2. 命令行模式

```bash
# 拍摄单张照片
./start_camera.sh --capture photo.jpg

# 录制视频（30秒）
./start_camera.sh --record video.avi --fps 25 --duration 30

# 连续拍照（每0.5秒一张，共100张）
./start_camera.sh --continuous photos --interval 0.5 --max-count 100

# 使用校准文件
./start_camera.sh --calibration ../calibration/20250910_232046/calibration_result.json
```

#### 3. 后台运行

```bash
# 后台录像
nohup ./start_camera.sh --record background_video.avi --duration 3600 > recording.log 2>&1 &

# 后台连续拍照
nohup ./start_camera.sh --continuous timelapse --interval 10 > capture.log 2>&1 &
```

## 校准文件

程序支持两种校准文件格式：

### JSON格式 (calibration_result.json)
```json
{
  "camera_matrix": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
  "distortion_coefficients": [k1, k2, p1, p2, k3],
  "calibration_info": {
    "image_size": [width, height]
  },
  "reprojection_error": 0.123456
}
```

### XML格式 (camera_parameters.xml)
```xml
<?xml version="1.0"?>
<opencv_storage>
<camera_matrix type_id="opencv-matrix">
  <rows>3</rows>
  <cols>3</cols>
  <dt>d</dt>
  <data>fx 0 cx 0 fy cy 0 0 1</data>
</camera_matrix>
<distortion_coefficients type_id="opencv-matrix">
  <rows>1</rows>
  <cols>5</cols>
  <dt>d</dt>
  <data>k1 k2 p1 p2 k3</data>
</distortion_coefficients>
</opencv_storage>
```

## 文件输出

### 目录结构
```
output/
├── photos/               # 单张照片
├── videos/               # 录制视频
├── continuous_capture/   # 连续拍照
└── logs/                # 日志文件
```

### 文件命名规则
- 单张照片: `capture_YYYYMMDD_HHMMSS.jpg`
- 录制视频: 用户指定或默认 `video.avi`
- 连续拍照: `capture_YYYYMMDD_HHMMSS_fff.jpg`

## 配置文件

编辑 `config.json` 可以修改默认设置：

```json
{
  "camera_settings": {
    "default_device_index": 0,
    "connection_timeout": 5000,
    "frame_timeout": 1000
  },
  "capture_settings": {
    "default_format": "jpg",
    "quality": 95,
    "apply_calibration": true
  },
  "video_settings": {
    "default_fps": 30,
    "default_codec": "XVID"
  }
}
```

## 故障排除

### 常见问题

#### 1. SDK导入失败
```
ImportError: No module named 'MvCameraControl_class'
```

**解决方案:**
- 确认SDK已正确安装到 `/opt/MVS/` 或 `/usr/local/MVS/`
- 运行 `source setup_env.sh` 设置环境变量
- 检查Python路径是否包含SDK目录

#### 2. 相机权限错误
```
Device open failed: Permission denied
```

**解决方案:**
```bash
# 对于USB相机
sudo usermod -a -G plugdev $USER
# 重新登录

# 对于GigE相机，检查防火墙设置
sudo systemctl stop firewalld  # CentOS
sudo ufw disable              # Ubuntu
```

#### 3. 网络配置问题（GigE相机）
```
Device enumeration failed
```

**解决方案:**
- 确认相机和主机在同一网段
- 设置网卡MTU为9000（巨型帧）
- 检查网络适配器缓冲区设置

#### 4. 图像获取超时
```
Get frame timeout
```

**解决方案:**
- 检查相机连接状态
- 增加超时时间设置
- 检查网络带宽（GigE相机）

### 日志分析

启用详细日志模式：
```bash
./start_camera.sh --verbose
```

或查看日志文件：
```bash
tail -f logs/camera_controller.log
```

### 性能优化

#### 1. 网络优化（GigE相机）
```bash
# 设置网卡缓冲区
sudo ethtool -G eth0 rx 4096 tx 4096

# 设置中断合并
sudo ethtool -C eth0 rx-usecs 50

# 禁用网卡节能
sudo ethtool -s eth0 autoneg off speed 1000 duplex full
```

#### 2. 系统优化
```bash
# 增加系统文件描述符限制
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# 优化内核参数
echo "net.core.rmem_max = 134217728" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max = 134217728" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

#### 3. Jetson性能优化

**设置最大性能模式：**
```bash
# 查看可用性能模式
sudo nvpmodel -q

# 设置为最大性能模式（模式0）
sudo nvpmodel -m 0

# 锁定最大CPU/GPU频率
sudo jetson_clocks

# 查看当前频率状态
sudo jetson_clocks --show
```

**温度和功耗监控：**
```bash
# 实时监控系统状态
sudo tegrastats

# 安装jetson-stats工具包（推荐）
sudo pip3 install jetson-stats
sudo jtop  # 图形化监控界面
```

**散热优化：**
```bash
# 设置风扇策略（如果有主动散热）
echo 255 | sudo tee /sys/devices/pwm-fan/target_pwm

# 监控温度
watch -n 1 'cat /sys/devices/virtual/thermal/thermal_zone*/temp'
```

**内存优化：**
```bash
# 禁用swap（提高性能）
sudo swapoff -a

# 清理内存缓存
echo 3 | sudo tee /proc/sys/vm/drop_caches
```

## 服务化部署

### 创建systemd服务

```bash
sudo tee /etc/systemd/system/hikvision-camera.service << EOF
[Unit]
Description=Hikvision Camera Controller
After=network.target

[Service]
Type=simple
User=camera
Group=camera
WorkingDirectory=/opt/camera_controller
ExecStart=/opt/camera_controller/start_camera.sh --record /var/log/camera/video.avi
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl enable hikvision-camera
sudo systemctl start hikvision-camera
```

### Docker部署

```dockerfile
FROM ubuntu:20.04

# 安装依赖
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    libopencv-dev python3-opencv \
    libusb-1.0-0-dev

# 复制程序文件
COPY . /app
WORKDIR /app

# 安装Python依赖
RUN pip3 install -r requirements.txt

# 设置权限
RUN chmod +x start_camera.sh

# 运行程序
CMD ["./start_camera.sh"]
```

## API参考

### CameraControllerLinux类

#### 方法说明

```python
# 初始化相机
controller = CameraControllerLinux()
controller.initialize_camera(device_index=0)

# 加载校准文件
controller.load_calibration("calibration.json")

# 拍照
controller._handle_capture("photo.jpg")

# 录像
controller._handle_record("video.avi", fps=30, codec="XVID")

# 连续拍照
controller._handle_continuous("photos", interval=1.0, format="jpg", max_count=100)
```

### HikvisionCameraLinux类

```python
# 创建相机对象
camera = HikvisionCameraLinux(calibration=calibration)

# 连接相机
camera.discover_devices()
camera.connect(device_index=0)
camera.start_grabbing()

# 获取图像
image = camera.capture_image("photo.jpg")

# 录像控制
camera.start_video_recording("video.avi", fps=30)
camera.stop_video_recording()

# 连续拍照
camera.start_continuous_capture("photos", interval=1.0)
camera.stop_continuous_capture()
```

## 更新日志

### v1.0.0 (2025-09-13)
- 初始Linux版本发布
- 支持图像获取、录像、连续拍照
- 支持JSON和XML校准文件
- 完整的命令行界面
- 自动安装脚本
- 服务化部署支持

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 技术支持

如需技术支持，请联系：
- 项目仓库: https://github.com/your-repo/hikvision-camera-controller
- 问题反馈: https://github.com/your-repo/hikvision-camera-controller/issues
- 邮箱: support@your-domain.com

## 贡献指南

欢迎提交问题报告和功能请求。如需贡献代码：

1. Fork项目仓库
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

---

**注意**: 本程序需要海康威视MVS SDK的支持。SDK的获取和使用需要遵循海康威视的许可协议。
