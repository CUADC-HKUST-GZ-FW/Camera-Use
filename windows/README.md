# 海康威视相机控制程序 - Windows版本

## 概述

这是海康威视相机控制程序的Windows版本，提供图形界面支持，包含实时预览功能。程序支持图像获取、视频录制、连续拍照等功能，并可加载相机校准参数进行图像去畸变处理。

## 功能特性

- **图形界面**: 实时预览相机画面
- **单张拍照**: 支持多种图像格式 (JPG, PNG, BMP, TIFF)
- **视频录制**: 支持多种编码格式 (XVID, MJPG, H264等)
- **连续拍照**: 可设定间隔时间和最大数量
- **校准支持**: 自动加载校准参数并进行图像去畸变
- **交互界面**: 完整的命令行交互功能
- **批处理模式**: 支持命令行参数直接执行任务

## 系统要求

### 硬件要求
- 海康威视工业相机（GigE或USB3.0接口）
- Windows 10/11 x64
- 至少2GB内存
- 1GB可用存储空间

### 软件要求
- Python 3.7+
- 海康威视MVS SDK
- OpenCV 4.5.0+
- NumPy 1.19.0+
- Visual Studio 2019+ 运行时库

## 安装指南

### 自动安装

运行安装脚本进行一键安装：

```cmd
install.bat
```

安装脚本会自动：
1. 检查Python版本
2. 安装Python依赖
3. 检查SDK安装状态
4. 配置环境

### 手动安装

#### 1. 安装海康威视MVS SDK

1. 从[海康威视官网](https://www.hikrobotics.com/cn/machinevision/service/download)下载Windows版本的MVS软件包
2. 安装MVS软件，默认路径：`C:\Program Files\MVS\`
3. 确保Python SDK路径正确：`C:\Program Files\MVS\Development\Samples\Python\MvImport`

#### 2. 安装Python依赖

```cmd
pip install -r requirements.txt
```

或使用镜像源：

```cmd
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

#### 3. 连接相机

- **GigE相机**：通过网线连接，配置同一网段IP
- **USB3.0相机**：直接USB连接

## 使用方法

### 快速启动

```cmd
# 使用启动脚本（推荐）
start_camera.bat

# 或直接运行Python程序
python hikvision_camera_controller.py
```

### 命令行选项

```cmd
python hikvision_camera_controller.py [选项]

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
  --preview                 启动实时预览
  --no-gui                  禁用图形界面
  --verbose, -v             详细输出模式
  --help, -h                显示帮助信息
```

### 使用示例

#### 1. 交互模式

```cmd
start_camera.bat
```

进入交互模式后，可以使用以下命令：

```
>>> capture photo.jpg          # 拍照
>>> record video.avi 25 MJPG   # 录像
>>> continuous photos 0.5 png 100  # 连续拍照
>>> calibration camera_parameters.xml  # 加载校准
>>> preview                    # 启动预览
>>> info                       # 显示相机信息
>>> status                     # 显示状态
>>> help                       # 显示帮助
>>> quit                       # 退出
```

#### 2. 命令行模式

```cmd
# 拍摄单张照片
start_camera.bat --capture photo.jpg

# 录制视频
start_camera.bat --record video.avi --fps 25

# 连续拍照
start_camera.bat --continuous photos --interval 0.5 --max-count 100

# 实时预览
start_camera.bat --preview

# 使用校准文件
start_camera.bat --calibration ..\calibration\20250910_232046\calibration_result.json
```

#### 3. 批处理模式

```cmd
# 批量拍照（10张，间隔2秒）
for /l %%i in (1,1,10) do (
    start_camera.bat --capture photo_%%i.jpg
    timeout /t 2 /nobreak >nul
)

# 定时录像（每小时录制5分钟）
start_camera.bat --record hourly_video.avi --duration 300
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
└── screenshots/          # 预览截图
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
  "gui_settings": {
    "window_size": [800, 600],
    "preview_fps": 30,
    "show_info_overlay": true
  },
  "capture_settings": {
    "default_format": "jpg",
    "quality": 95,
    "apply_calibration": true
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
- 确认MVS SDK已正确安装到 `C:\Program Files\MVS\`
- 检查Python版本兼容性（需要3.7+）
- 确认SDK Python路径正确

#### 2. 相机连接失败
```
Device open failed: Access denied
```

**解决方案:**
- 检查相机是否被其他程序占用
- 确认相机驱动已安装
- 重启相机设备

#### 3. 图形界面问题
```
cv2.error: The function is not implemented
```

**解决方案:**
- 安装完整版OpenCV：`pip install opencv-python`
- 更新显卡驱动
- 使用 `--no-gui` 参数禁用图形界面

#### 4. 网络配置问题（GigE相机）
```
Device enumeration timeout
```

**解决方案:**
- 确认相机和主机在同一网段
- 检查网络适配器设置
- 关闭Windows防火墙

### 日志分析

启用详细日志模式：
```cmd
start_camera.bat --verbose
```

查看日志文件：
```cmd
type logs\camera_controller.log
```

### 性能优化

#### 1. 提高帧率
- 降低分辨率设置
- 使用硬件编码（H264）
- 优化网络缓冲区

#### 2. 减少延迟
- 设置相机为连续采集模式
- 使用较小的图像格式
- 关闭不必要的图像处理

## 高级功能

### 1. 多相机支持

```cmd
# 连接多个相机
start_camera.bat --device 0 &
start_camera.bat --device 1 &
```

### 2. 自动化脚本

创建批处理文件实现自动化：

```batch
@echo off
REM 自动化拍照脚本
for /l %%i in (1,1,100) do (
    echo 正在拍摄第 %%i 张照片...
    start_camera.bat --capture auto_%%i.jpg --no-gui
    timeout /t 5 /nobreak >nul
)
echo 拍照完成！
```

### 3. 定时任务

使用Windows任务计划程序创建定时任务：

```cmd
# 创建每日定时录像任务
schtasks /create /tn "DailyRecording" /tr "C:\path\to\start_camera.bat --record daily.avi --duration 3600" /sc daily /st 09:00
```

## 服务化部署

### 使用NSSM创建Windows服务

1. 下载NSSM (Non-Sucking Service Manager)
2. 创建服务：

```cmd
nssm install HikvisionCamera
nssm set HikvisionCamera Application "C:\path\to\start_camera.bat"
nssm set HikvisionCamera Parameters "--record service_video.avi"
nssm set HikvisionCamera DisplayName "Hikvision Camera Service"
nssm set HikvisionCamera Description "海康威视相机控制服务"
nssm start HikvisionCamera
```

### Docker容器化（实验性）

```dockerfile
FROM python:3.9-windowsservercore

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制程序文件
COPY . /app
WORKDIR /app

# 运行程序
CMD ["python", "hikvision_camera_controller.py", "--no-gui"]
```

## API参考

### CameraController类

#### 方法说明

```python
# 初始化相机
controller = CameraController()
controller.initialize_camera(device_index=0)

# 加载校准文件
controller.load_calibration("calibration.json")

# 拍照
controller._handle_capture("photo.jpg")

# 录像
controller._handle_record("video.avi", fps=30, codec="XVID")

# 预览
controller._handle_preview()
```

### HikvisionCamera类

```python
# 创建相机对象
camera = HikvisionCamera(calibration=calibration)

# 连接相机
camera.discover_devices()
camera.connect(device_index=0)
camera.start_grabbing()

# 获取图像
image = camera.capture_image("photo.jpg")

# 预览控制
camera.start_preview()
camera.stop_preview()
```

## 更新日志

### v1.0.0 (2025-09-13)
- 初始Windows版本发布
- 支持图像获取、录像、连续拍照
- 图形界面和实时预览功能
- 支持JSON和XML校准文件
- 完整的命令行界面
- 自动安装脚本

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
