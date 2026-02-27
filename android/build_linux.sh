#!/bin/bash
# Linux/Mac 下快速打包和安装脚本

echo "========================================"
echo "微信跳一跳 Android 助手 - 打包工具"
echo "========================================"
echo ""

echo "[1] 检查环境"
python3 --version
echo ""

echo "[2] 安装依赖"
pip3 install -r requirements.txt
echo ""

echo "[3] 打包 APK (仅 armeabi-v7a，兼容性最好)"
python3 -m pythonforandroid.toolchain apk --private \
    --name="跳一跳助手" \
    --version=1.0 \
    --package=com.jumpjump.auto \
    --bootstrap=sdl2 \
    --requirements=kivy,opencv-python-headless,pillow,pyjnius \
    --arch=armeabi-v7a \
    --orientations=portrait \
    main.py
echo ""

echo "[4] 安装到手机"
echo "请连接手机并授权 ADB，然后按 Enter 继续..."
read
python3 -m pythonforandroid.toolchain adb install \
    --package=com.jumpjump.auto \
    --name="跳一跳助手"
echo ""

echo "完成！"
