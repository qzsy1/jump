# -*- coding: utf-8 -*-
"""
APK 打包脚本
使用 python-for-android 打包 Kivy 应用为 APK
"""
import os
import sys

# 要打包的设备架构（armeabi-v7a most common）
archs = 'armeabi-v7a arm64-v8a'.split()

# SDK 和 NDK 版本
android_api = 33
ndk_version = '25b'

# 要打包的模块
requirements = [
    'kivy',
    'opencv-python-headless',
    'pillow',
    'pyjnius',
    'android'
]

# 打包命令
build_command = f"""python -m pythonforandroid.toolchain apk --private \
    --name="跳一跳助手" \
    --version=1.0 \
    --package=com.jumpjump.auto \
    --bootstrap=sdl2 \
    --requirements={','.join(requirements)} \
    --android-api={android_api} \
    --ndk-version={ndk_version} \
    --arch={archs} \
    --orientations=portrait \
    --permission=INTERNET \
    --permission=WRITE_EXTERNAL_STORAGE \
    --permission=READ_EXTERNAL_STORAGE \
    main.py"""

print("=" * 70)
print("APK 打包说明")
print("=" * 70)
print("""
前置条件:
1. 安装 python-for-android: pip install python-for-android
2. 安装 JDK 8 或更高版本
3. 安装 Android SDK
4. 配置 ANDROID_SDK 和 ANDROID_NDK 环境变量
5. 手机开启 USB 调试

打包步骤:
1. 连接 Android 手机并授权 ADB
2. 运行以下命令:

# 简单打包（仅 armeabi-v7a）
python -m pythonforandroid.toolchain apk --private \\
    --name="跳一跳助手" \\
    --version=1.0 \\
    --package=com.jumpjump.auto \\
    --bootstrap=sdl2 \\
    --requirements=kivy,opencv-python-headless,pillow,pyjnius \\
    --arch=armeabi-v7a \\
    --orientations=portrait \\
    main.py

# 调试安装到手机
python -m pythonforandroid.toolchain adb install \\
    --package=com.jumpjump.auto \\
    --name="跳一跳助手" \\
    --arch=armeabi-v7a
""")

print("\n" + "=" * 70)
print("点击下方按钮生成完整打包命令...")
print("=" * 70)

# 生成完整命令
print(f"\n生成的完整命令:\n{build_command}\n")

print("\n注意事项:")
print("1. 首次打包需要下载较多依赖，请耐心等待")
print("2. 如果遇到权限问题，请在手机上手动授权")
print("3. 建议先在模拟器上测试")
