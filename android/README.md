# 微信跳一跳 Android 助手

## 功能说明

- 基于 Python + Kivy 框架开发
- 核心算法移植自 [wangshub/wechat_jump_game](https://github.com/wangshub/wechat_jump_game)
- 可直接打包为 APK 在 Android 手机运行

## 主要功能

1. **分辨率自定义输入**：用户直接输入屏幕分辨率（格式：宽x高，如 1080x1920）
2. **一键开始**：点击开始后界面最小化，只显示悬浮停止按钮
3. **自动跳跃**：使用 adb 截图 + 图像识别 + 自动按压
4. **停止恢复**：点击停止按钮后恢复主界面

## 依赖安装

```bash
pip install kivy[base]
pip install python-for-android
pip install opencv-python-headless
pip install pillow
```

## 打包 APK

```bash
p4a apk --private --package=com.jumpjump.auto --name "跳一跳助手" --version 1.0 --bootstrap=sdl2 --requirements=opencv-python-headless,pillow main.py
```

## 使用方法

1. 手机开启 USB 调试
2. 连接电脑，授权 ADB
3. 安装并打开 APK
4. **输入手机屏幕分辨率**（如：1080x1920）
5. 打开微信跳一跳游戏
6. 点击开始按钮
7. 程序自动运行，点击悬浮按钮停止

## 分辨率输入格式

**格式**：`宽x高` 或 `宽X高`

**示例**：
- 720x1280（通用720p）
- 1080x1920（通用1080p）
- 1080x2340（华为P40）
- 1080x2400（小米/三星/OPPO）
- 1170x2532（iPhone 13）
- 1440x3200（2K屏）

## 查找分辨率方法

1. 设置 → 关于手机 → 屏幕分辨率
2. 在线搜索：手机型号 + "分辨率"

详细使用说明请查看 [USAGE.md](USAGE.md)
