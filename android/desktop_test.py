# -*- coding: utf-8 -*-
"""
桌面测试脚本 - 在电脑上预览界面效果
"""
import os
from kivy.core.window import Window

# 设置窗口大小（模拟手机屏幕）
Window.size = (540, 960)

# 导入主应用
from main import JumpApp

if __name__ == '__main__':
    # 运行应用
    JumpApp().run()
