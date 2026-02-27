# Android 版本创建完成

## 创建的文件

```
C:\Users\xlq\jump_jump_auto\android\
├── main.py              # 主程序（Kivy 界面 + wangshub 核心算法）
├── jump.kv             # Kivy 界面样式定义
├── build.py            # 打包说明脚本
├── build_windows.bat   # Windows 一键打包脚本
├── build_linux.sh      # Linux/Mac 一键打包脚本
├── requirements.txt     # Python 依赖列表
├── desktop_test.py     # 桌面预览测试脚本
├── Makefile            # Make 构建命令
├── README.md           # 项目说明
└── USAGE.md            # 完整使用说明
```

## 核心特性

### 1. 分辨率自定义输入
- 用户直接输入屏幕分辨率（格式：宽x高，如 1080x1920）
- 支持小写 x 或大写 X
- 自动根据分辨率估算 DPI
- 提供常见分辨率提示

### 2. 一键开始/悬浮窗模式
- 点击开始后界面自动最小化
- 只显示一个悬浮停止按钮
- 不遮挡游戏视野

### 3. 完整移植 wangshub 核心算法
- 棋子颜色检测（精确RGB范围）
- 平台检测（抗干扰机制）
- 对称中心计算（delta_piece_y）
- 二次曲线按压时间公式

### 4. 参数可调
- 按压系数滑块：0.5 - 3.0
- 实时显示当前配置

## 快速使用流程

### 步骤1：打包 APK
```bash
cd C:\Users\xlq\jump_jump_auto\android
build_windows.bat    # Windows
# 或
chmod +x build_linux.sh && ./build_linux.sh    # Linux/Mac
```

### 步骤2：安装到手机
```bash
# 连接手机后自动安装
adb install bin/跳一跳助手-1.0-armeabi-v7a-debug.apk
```

### 步骤3：运行程序
1. 打开"跳一跳助手"应用
2. **输入手机屏幕分辨率**（如：1080x1920）
3. 点击"开始"
4. 界面消失，出现悬浮停止按钮
5. 打开微信 → 跳一跳 → 开始游戏
6. 程序自动运行

### 步骤4：调整参数
- 如果跳太近：增大按压系数
- 如果跳太远：减小按压系数

## 分辨率输入格式

| 格式 | 示例 | 说明 |
|------|------|------|
| 宽x高 | 1080x1920 | 小写x |
| 宽X高 | 1080X1920 | 大写X |

### 常见分辨率
- 720x1280（通用720p）
- 1080x1920（通用1080p）
- 1080x2340（华为P40）
- 1080x2400（小米/三星/OPPO）
- 1170x2532（iPhone 13）
- 1440x3200（2K屏）

## 技术栈

- **框架**: Kivy (Python 跨平台)
- **打包工具**: python-for-android
- **核心算法**: wangshub/wechat_jump_game
- **图像处理**: Pillow + OpenCV
- **Android ADB**: 系统调用

## 系统要求

**开发电脑**:
- Python 3.8+
- JDK 8+
- Android SDK
- python-for-android

**Android 手机**:
- Android 5.0+ (推荐 7.0+)
- 支持 USB 调试
- 约 50MB 存储空间

## 常见问题

**Q: ADB 连接失败**
A:
1. 手机开启 USB 调试
2. 允许 USB 调试授权
3. 更换 USB 端口或线

**Q: APK 安装失败**
A:
1. 设置中允许"未知来源"
2. 卸载旧版本
3. 检查 Android 版本

**Q: 悬浮按钮无法点击**
A:
1. 应用管理 → 跳一跳助手 → 权限
2. 开启"显示在其他应用上层"

**Q: 跳跃不准确**
A:
1. 检查分辨率输入是否正确
2. 调整按压系数
3. 确保游戏在最前台

**Q: 如何查找手机分辨率**
A:
1. 设置 → 关于手机 → 屏幕分辨率
2. 或在线搜索你的手机型号 + "分辨率"
