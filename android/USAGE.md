# 微信跳一跳 Android 助手 - 完整使用说明

## 目录结构

```
android/
├── main.py              # 主程序
├── jump.kv             # 界面样式定义
├── build.py            # 打包说明脚本
├── build_windows.bat   # Windows 打包脚本
├── build_linux.sh      # Linux/Mac 打包脚本
├── requirements.txt     # 依赖列表
└── README.md           # 本说明文档
```

---

## 快速开始

### 方法一：直接安装 APK（最简单）

1. **手机准备**
   - 进入手机设置 → 关于手机 → 连续点击"版本号"7次
   - 返回设置 → 开发者选项 → 开启"USB调试"
   - 用 USB 线连接电脑

2. **电脑端操作**
   ```bash
   # Windows 运行
   build_windows.bat

   # Linux/Mac 运行
   chmod +x build_linux.sh
   ./build_linux.sh
   ```

3. **手机授权**
   - 手机会弹出"允许USB调试吗？"，点击"确定"
   - 在手机上安装 APK 后，授予存储权限

4. **运行程序**
   - 打开"跳一跳助手"应用
   - **输入手机屏幕分辨率**（格式：宽x高，如 1080x1920）
   - 调整按压系数（默认2.0）
   - 点击"开始"
   - 界面最小化，只显示悬浮停止按钮
   - 打开微信跳一跳，程序自动跳跃

### 方法二：Python 脚本运行（开发调试）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 连接手机并授权 ADB
adb devices

# 3. 直接运行（需要手机已连接）
python main.py
```

---

## 详细步骤

### 一、环境准备

#### Windows 系统
```bash
# 1. 安装 Python 3.8+
# 下载: https://www.python.org/downloads/

# 2. 安装依赖
pip install kivy[base] opencv-python-headless pillow pyjnius

# 3. 安装 python-for-android
pip install python-for-android
```

#### Linux/Mac 系统
```bash
# 1. 安装 Python 3.8+
sudo apt install python3 python3-pip

# 2. 安装依赖
pip3 install kivy[base] opencv-python-headless pillow pyjnius

# 3. 安装 python-for-android
pip3 install python-for-android
```

### 二、打包 APK

#### Windows
```bash
# 运行打包脚本
build_windows.bat

# 或手动打包
python -m pythonforandroid.toolchain apk \\
    --private \\
    --name="跳一跳助手" \\
    --version=1.0 \\
    --package=com.jumpjump.auto \\
    --bootstrap=sdl2 \\
    --requirements=kivy,opencv-python-headless,pillow,pyjnius \\
    --arch=armeabi-v7a \\
    --orientations=portrait \\
    main.py
```

#### Linux/Mac
```bash
# 运行打包脚本
chmod +x build_linux.sh
./build_linux.sh

# 或手动打包
python3 -m pythonforandroid.toolchain apk \\
    --private \\
    --name="跳一跳助手" \\
    --version=1.0 \\
    --package=com.jumpjump.auto \\
    --bootstrap=sdl2 \\
    --requirements=kivy,opencv-python-headless,pillow,pillow \\
    --arch=armeabi-v7a \\
    --orientations=portrait \\
    main.py
```

**打包输出位置**: `bin/跳一跳助手-1.0-armeabi-v7a-debug.apk`

### 三、安装到手机

#### 方法1：通过 ADB 安装（推荐）
```bash
# 连接手机并授权后
adb install bin/跳一跳助手-1.0-armeabi-v7a-debug.apk
```

#### 方法2：直接传输 APK
- 将 APK 文件复制到手机存储
- 在手机上点击 APK 文件进行安装
- 如提示"禁止安装未知来源应用"，需在设置中允许

### 四、运行程序

#### 首次使用
1. 打开"跳一跳助手"
2. **选择手机型号**（支持常见品牌）
3. **调整按压系数**（默认2.0，可根据实际效果调整）
4. **点击"开始"**

#### 自动运行模式
- 界面自动最小化
- **只显示一个悬浮停止按钮**
- 打开微信 → 跳一跳 → 开始游戏
- 程序自动检测并跳跃

#### 停止程序
- 点击悬浮的"■ 停止"按钮
- 界面恢复正常，可重新配置

---

## 分辨率输入说明

### 输入格式
- **格式**：`宽x高`（小写x或大写X均可）
- **示例**：`1080x1920`、`720x1280`、`1170x2532`

### 查找手机分辨率的方法
1. **设置 → 关于手机 → 屏幕分辨率**
2. **在线查询**：搜索你的手机型号 + "分辨率"

### 常见分辨率参考

| 分辨率 | 适用机型 |
|--------|----------|
| 720x1280 | 通用720p手机 |
| 1080x1920 | 通用1080p手机 |
| 1080x2340 | 华为P40/Mate 40 |
| 1080x2400 | 小米11/12/13、三星S21/S22、OPPO |
| 1080x2412 | OPPO Find X3/X5 |
| 1080x2408 | vivo X70 Pro/X90 |
| 1170x2532 | iPhone 13 |
| 1179x2556 | iPhone 14 Pro |
| 1440x2560 | 2K屏幕 |
| 1440x3200 | 2K高分屏 |

**注意事项**：
- 程序会自动根据分辨率估算DPI值
- 输入格式错误时会提示重新输入

---

## 参数调整说明

### 按压系数（Press Coefficient）

| 系数值 | 适用场景 |
|--------|----------|
| 0.8 - 1.2 | 距离偏大，跳太远 |
| 1.5 - 2.0 | **默认推荐**，大多数情况 |
| 2.2 - 3.0 | 距离偏小，跳太近 |

**调整建议**：
- 先用默认值 2.0 测试
- 观察第一次跳跃：
  - **跳太近** → 增大系数（2.0 → 2.2）
  - **跳太远** → 减小系数（2.0 → 1.8）
- 重复微调直到准确

---

## 常见问题

### Q1: ADB 无法连接设备
**解决方法**：
1. 检查 USB 线是否连接
2. 手机是否开启 USB 调试
3. 运行 `adb devices` 查看设备列表
4. 尝试更换 USB 端口或线

### Q2: APK 安装失败
**解决方法**：
1. 检查"允许安装未知来源"是否开启
2. 卸载旧版本后重新安装
3. 检查 Android 版本（建议 Android 7.0+）

### Q3: 程序无法检测棋子或平台
**解决方法**：
1. 确保微信跳一跳游戏在最前台
2. 手机屏幕亮度适中，不要太暗
3. 检查是否有截图权限

### Q4: 悬浮按钮无法点击
**解决方法**：
1. 检查是否授予悬浮窗权限
2. 在设置 → 应用管理 → 跳一跳助手 → 权限中开启

### Q5: 每次跳跃距离都不一样
**解决方法**：
1. 检查是否选择了正确的手机型号
2. 如果不在列表中，选择通用分辨率并微调系数
3. 尝试在不同位置测试，取平均效果

---

## 核心算法说明

本程序核心算法完全移植自 [wangshub/wechat_jump_game](https://github.com/wangshub/wechat_jump_game)，包括：

1. **棋子检测**：精确的 RGB 颜色范围 `(50,53,95) - (60,63,110)`
2. **平台检测**：带抗干扰机制的亮色检测
3. **对称中心计算**：用于计算 delta_piece_y
4. **二次曲线按压时间公式**：基于物理推导的精确算法

---

## 开源许可

- 核心算法：MIT License (来自 wangshub/wechat_jump_game)
- 界面代码：MIT License

---

## 更新日志

### v1.0 (2024-02-27)
- ✅ 初始版本
- ✅ 支持 Android 手机直接运行
- ✅ 悬浮窗模式
- ✅ 完整移植 wangshub 核心算法
