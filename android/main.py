# -*- coding: utf-8 -*-
"""
微信跳一跳 Android 助手 - 主程序
基于 Kivy 框架，核心算法移植自 wangshub/wechat_jump_game
"""
import os
import sys
import time
import math
import subprocess
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from PIL import Image
import cv2

# Android 特定导入
try:
    from jnius import autoclass
    from android.permissions import Permission, request_permissions
    ANDROID = True
except ImportError:
    ANDROID = False
    print("Warning: Not running on Android, using desktop mode")

# 添加 TextInput 导入
from kivy.uix.textinput import TextInput


# ==================== 分辨率参考提示 ====================
RESOLUTION_HINTS = [
    "720x1280 (通用720p)",
    "1080x1920 (通用1080p)",
    "1080x2340 (华为P40)",
    "1080x2400 (小米/三星)",
    "1170x2532 (iPhone 13)",
    "1440x3200 (2K屏)",
]


# ==================== 核心算法类（移植自wangshub） ====================
class JumpConfig:
    """跳一跳配置"""
    def __init__(self):
        # 长按的时间系数
        self.press_coefficient = 2.0

        # 二分之一的棋子底座高度
        self.piece_base_height_1_2 = 20

        # 棋子的宽度
        self.piece_body_width = 70

        # 棋子头部直径（像素）
        self.head_diameter = 135


class JumpAlgorithm:
    """跳跃算法核心类 - 完整移植自 wangshub/wechat_jump_game"""

    def __init__(self, config: JumpConfig):
        self.config = config

    def find_piece_and_board(self, screenshot_path):
        """
        寻找关键坐标 - 移植自 wangshub wechat_jump_auto.py 第103-197行
        """
        im = Image.open(screenshot_path)
        w, h = im.size
        im_pixel = im.load()

        points = []
        piece_y_max = 0
        board_x = 0
        board_y = 0

        # 扫描棋子时的左右边界
        scan_x_border = int(w / 8)
        scan_start_y = 0

        # 以50px步长，尝试探测scan_start_y
        for i in range(int(h / 3), int(h * 2 / 3), 50):
            last_pixel = im_pixel[0, i]
            for j in range(1, w):
                pixel = im_pixel[j, i]
                if pixel != last_pixel:
                    scan_start_y = i - 50
                    break
            if scan_start_y:
                break

        print(f"start scan Y axis: {scan_start_y}")

        # 从scan_start_y开始往下扫描
        for i in range(scan_start_y, int(h * 2 / 3)):
            for j in range(scan_x_border, w - scan_x_border):
                pixel = im_pixel[j, i]
                # 根据棋子的最低行的颜色判断（精确RGB范围）
                if (50 < pixel[0] < 60) and (53 < pixel[1] < 63) and (95 < pixel[2] < 110):
                    points.append((j, i))
                    piece_y_max = max(i, piece_y_max)

        if not points:
            return None

        # 所有最底层的点的横坐标
        bottom_x = [x for x, y in points if y == piece_y_max]
        if not bottom_x:
            return None

        piece_x = int(sum(bottom_x) / len(bottom_x))
        piece_y = piece_y_max - self.config.piece_base_height_1_2

        # 限制棋盘扫描的横坐标
        if piece_x < w / 2:
            board_x_start = piece_x
            board_x_end = w
        else:
            board_x_start = 0
            board_x_end = piece_x

        # 扫描平台中心
        for i in range(int(h / 3), int(h * 2 / 3)):
            last_pixel = im_pixel[0, i]
            if board_x or board_y:
                break
            board_x_sum = 0
            board_x_c = 0

            for j in range(int(board_x_start), int(board_x_end)):
                pixel = im_pixel[j, i]
                # 修掉脑袋比下一个小格子还高的情况的bug
                if abs(j - piece_x) < self.config.piece_body_width:
                    continue

                # 检查Y轴下面5个像素（抗干扰）
                ver_pixel = im_pixel[j, i + 5]
                if abs(pixel[0] - last_pixel[0]) + abs(pixel[1] - last_pixel[1]) + abs(pixel[2] - last_pixel[2]) > 10 \
                        and abs(ver_pixel[0] - last_pixel[0]) + abs(ver_pixel[1] - last_pixel[1]) + abs(ver_pixel[2] - last_pixel[2]) > 10:
                    board_x_sum += j
                    board_x_c += 1
            if board_x_sum:
                board_x = board_x_sum / board_x_c

        last_pixel = im_pixel[board_x, i]

        # 计算对称中心（用于delta_piece_y）
        center_x = w / 2 + (24 / 1080) * w
        center_y = h / 2 + (17 / 1920) * h

        if piece_x > center_x:
            board_y = round((25.5 / 43.5) * (board_x - center_x) + center_y)
            delta_piece_y = piece_y - round((25.5 / 43.5) * (piece_x - center_x) + center_y)
        else:
            board_y = round(-(25.5 / 43.5) * (board_x - center_x) + center_y)
            delta_piece_y = piece_y - round(-(25.5 / 43.5) * (piece_x - center_x) + center_y)

        im.close()

        if not all((board_x, board_y)):
            return None

        return piece_x, piece_y, board_x, board_y, delta_piece_y

    def calculate_press_time(self, distance, delta_piece_y):
        """
        计算按压时间 - 移植自 wangshub wechat_jump_auto.py 第78-100行
        """
        # 计算程序长度与截图测得的距离的比例
        scale = 0.945 * 2 / self.config.head_diameter
        actual_distance = distance * scale * (math.sqrt(6) / 2)
        press_time = (-945 + math.sqrt(945 ** 2 + 4 * 105 *
                                       36 * actual_distance)) / (2 * 105) * 1000
        press_time *= self.config.press_coefficient
        press_time += delta_piece_y
        press_time = max(press_time, 200)
        press_time = int(press_time)

        return press_time


# ==================== ADB 操作类 ====================
class ADBController:
    """ADB 控制器"""

    def __init__(self):
        self.test_connection()

    def test_connection(self):
        """测试 ADB 连接"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            if 'device' in result.stdout:
                print("ADB 连接成功")
                return True
            else:
                print("ADB 未检测到设备，请确保 USB 调试已开启")
                return False
        except FileNotFoundError:
            print("ADB 未安装或不在 PATH 中")
            return False

    def screenshot(self, output_path):
        """截屏"""
        subprocess.run(['adb', 'shell', 'screencap', '-p', '/sdcard/screenshot.png'],
                       capture_output=True)
        subprocess.run(['adb', 'pull', '/sdcard/screenshot.png', output_path],
                       capture_output=True)

    def tap(self, x, y, duration_ms):
        """模拟按压"""
        # 将屏幕坐标转换为实际设备坐标
        # 使用 swipe 实现长按效果
        subprocess.run(['adb', 'shell', 'input', 'swipe', str(x), str(y), str(x), str(y),
                        str(duration_ms)], capture_output=True)


# ==================== Kivy 界面 ====================
class FloatingButton(FloatLayout):
    """悬浮停止按钮"""

    def __init__(self, stop_callback, **kwargs):
        super().__init__(**kwargs)
        self.stop_callback = stop_callback

        # 半透明背景
        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 0.8)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        # 停止按钮
        self.stop_btn = Button(
            text="■ 停止",
            size_hint=(None, None),
            size=(120, 80),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=20
        )
        self.stop_btn.bind(on_press=self.stop_callback)
        self.add_widget(self.stop_btn)

        # 状态标签
        self.status_label = Label(
            text="运行中...",
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.3},
            color=(1, 1, 1, 1),
            font_size=16
        )
        self.add_widget(self.status_label)


class MainScreen(BoxLayout):
    """主界面"""

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10

        # 标题
        self.add_widget(Label(
            text="微信跳一跳助手",
            size_hint=(1, None),
            height=60,
            font_size=28,
            bold=True
        ))

        # 分辨率输入
        self.add_widget(Label(
            text="输入屏幕分辨率（格式：宽x高，如 1080x1920）：",
            size_hint=(1, None),
            halign='left',
            font_size=16
        ))

        self.resolution_input = TextInput(
            text='1080x1920',
            hint_text='请输入分辨率，如 1080x1920',
            size_hint=(1, None),
            height=50,
            multiline=False,
            input_type='text',
            font_size=18
        )
        self.add_widget(self.resolution_input)

        # 显示选中配置
        self.config_label = Label(
            text="当前分辨率: 1080x1920",
            size_hint=(1, None),
            halign='left',
            font_size=14,
            color=(0.5, 0.5, 0.5, 1)
        )
        self.add_widget(self.config_label)

        # 常见分辨率提示
        self.add_widget(Label(
            text="常见分辨率: " + " | ".join(RESOLUTION_HINTS[:3]),
            size_hint=(1, None),
            halign='left',
            font_size=12,
            color=(0.6, 0.6, 0.6, 1),
            text_size=(None, None)
        ))

        self.resolution_input.bind(text=self.on_resolution_input)

        # 按压系数
        self.add_widget(Label(
            text="按压系数：",
            size_hint=(1, None),
            halign='left',
            font_size=16
        ))

        # 系数滑块
        from kivy.uix.slider import Slider
        self.coeff_slider = Slider(
            min=0.5,
            max=3.0,
            value=2.0,
            step=0.1,
            size_hint=(1, None),
            height=40
        )
        self.add_widget(self.coeff_slider)

        # 系数值显示
        self.coeff_label = Label(
            text="2.00",
            size_hint=(1, None),
            height=30,
            font_size=18
        )
        self.add_widget(self.coeff_label)

        self.coeff_slider.bind(value=self.on_coeff_change)

        # 开始按钮
        self.start_btn = Button(
            text="开始",
            size_hint=(1, None),
            height=60,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=22
        )
        self.start_btn.bind(on_press=self.start_jump)
        self.add_widget(self.start_btn)

        # 日志显示
        self.log_label = Label(
            text="等待开始...",
            size_hint=(1, 1),
            halign='left',
            valign='top',
            color=(0.3, 0.3, 0.3, 1)
        )
        self.add_widget(self.log_label)

    def on_resolution_input(self, text_input, value):
        """分辨率输入回调"""
        text = value.strip()
        self.config_label.text = f"当前分辨率: {text}"

    def parse_resolution(self, resolution_str):
        """解析分辨率字符串，返回模型字典"""
        text = resolution_str.strip()
        try:
            # 支持 "1080x1920" 或 "1080X1920" 格式
            if 'x' in text.lower():
                parts = text.lower().split('x')
                if len(parts) == 2:
                    width = int(parts[0].strip())
                    height = int(parts[1].strip())
                    # 根据分辨率估算 DPI
                    if width >= 1440:
                        density = 640
                    elif width >= 1170:
                        density = 460
                    elif width >= 1080:
                        density = 480
                    elif width >= 720:
                        density = 320
                    else:
                        density = 320
                    return {
                        'width': width,
                        'height': height,
                        'density': density,
                        'name': f'{width}x{height}'
                    }
        except (ValueError, IndexError):
            pass
        return None

    def on_coeff_change(self, slider, value):
        """系数滑块回调"""
        self.coeff_label.text = f"{value:.2f}"
        self.app.set_coefficient(value)

    def start_jump(self, instance):
        """开始跳跃"""
        resolution_str = self.resolution_input.text.strip()
        model = self.parse_resolution(resolution_str)

        if not model:
            self.show_popup("分辨率格式错误！\n请输入格式如：1080x1920")
            return

        # 设置模型
        self.app.set_model(model)

        # 切换到悬浮界面
        self.app.show_floating()

    def show_popup(self, message):
        """显示弹窗"""
        popup = Popup(
            title='提示',
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()
        Clock.schedule_once(popup.dismiss, 2)

    def update_log(self, message):
        """更新日志"""
        self.log_label.text = message


class JumpApp(App):
    """主应用类"""

    def __init__(self):
        super().__init__()
        self.current_model = None
        self.current_coefficient = 2.0
        self.is_running = False
        self.config = JumpConfig()
        self.algorithm = JumpAlgorithm(self.config)
        self.adb = ADBController()
        self.screenshot_path = "/sdcard/jump_screenshot.png"
        self.local_screenshot = "screenshot.png"

    def build(self):
        """构建界面"""
        self.main_screen = MainScreen(self)
        return self.main_screen

    def set_model(self, model):
        """设置手机型号"""
        self.current_model = model

    def get_model(self):
        """获取当前手机型号"""
        return self.current_model

    def set_coefficient(self, value):
        """设置按压系数"""
        self.current_coefficient = value
        self.config.press_coefficient = value

    def show_floating(self):
        """显示悬浮界面"""
        self.is_running = True
        self.floating = FloatingButton(stop_callback=self.stop_jump)

        # 设置全屏悬浮
        Window.fullscreen = True
        Window.borderless = True
        Window.background_color = (0, 0, 0, 0)

        self.root_window = self.root
        self.root.clear_widgets()
        self.root.add_widget(self.floating)

        # 开始自动跳跃循环
        Clock.schedule_interval(self.auto_jump_loop, 1.0)

    def stop_jump(self, instance):
        """停止跳跃"""
        self.is_running = False
        Clock.unschedule(self.auto_jump_loop)

        # 恢复主界面
        Window.fullscreen = False
        Window.borderless = False
        Window.background_color = (1, 1, 1, 1)

        self.root.clear_widgets()
        self.root.add_widget(self.main_screen)
        self.main_screen.update_log("已停止")

    def auto_jump_loop(self, dt):
        """自动跳跃循环"""
        if not self.is_running:
            return

        try:
            # 截图
            self.adb.screenshot(self.local_screenshot)

            # 识别位置
            result = self.algorithm.find_piece_and_board(self.local_screenshot)

            if result is None:
                self.floating.status_label.text = "检测失败"
                return

            piece_x, piece_y, board_x, board_y, delta_piece_y = result

            # 计算距离
            distance = math.sqrt((board_x - piece_x) ** 2 + (board_y - piece_y) ** 2)

            # 计算按压时间
            press_time = self.algorithm.calculate_press_time(distance, delta_piece_y)

            # 执行跳跃
            self.adb.tap(int(board_x), int(board_y), press_time)

            # 更新状态
            self.floating.status_label.text = f"距离: {distance:.0f}px | 按压: {press_time}ms"

            # 等待落地
            time.sleep(1.2)

        except Exception as e:
            self.floating.status_label.text = f"错误: {str(e)}"
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


# ==================== 启动 ====================
if __name__ == '__main__':
    JumpApp().run()
