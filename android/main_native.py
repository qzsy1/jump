# -*- coding: utf-8 -*-
"""
微信跳一跳 Android 原生版
直接在手机上运行，使用 Android 原生 API 截屏和模拟触摸
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from PIL import Image
import os
import subprocess
import math
import threading
import time

# Android 特定导入
try:
    from jnius import autoclass
    from android.permissions import Permission, request_permissions
    from android.storage import primary_external_storage_path
    Android = True
except ImportError:
    Android = False
    print("非 Android 环境")


# ==================== 常见分辨率 ====================
COMMON_RESOLUTIONS = [
    "720x1280",
    "1080x1920",
    "1080x2160",
    "1080x2340",
    "1080x2400",
    "1170x2532",
    "1179x2556",
    "1440x2560",
    "1440x3200",
]


# ==================== 核心配置 ====================
class JumpConfig:
    def __init__(self):
        self.press_coefficient = 2.0
        self.piece_base_height_1_2 = 20
        self.piece_body_width = 70
        self.head_diameter = 135


# ==================== 核心算法 ====================
class JumpAlgorithm:
    def __init__(self, config):
        self.config = config

    def find_piece_and_board(self, screenshot_path):
        """识别棋子和平台位置"""
        try:
            im = Image.open(screenshot_path)
            w, h = im.size
            im_pixel = im.load()

            points = []
            piece_y_max = 0
            board_x = 0
            board_y = 0

            # 扫描起始点
            scan_x_border = int(w / 8)
            scan_start_y = 0

            for i in range(int(h / 3), int(h * 2 / 3), 50):
                last_pixel = im_pixel[0, i]
                for j in range(1, w):
                    pixel = im_pixel[j, i]
                    if pixel != last_pixel:
                        scan_start_y = i - 50
                        break
                if scan_start_y:
                    break

            # 扫描棋子
            for i in range(scan_start_y, int(h * 2 / 3)):
                for j in range(scan_x_border, w - scan_x_border):
                    pixel = im_pixel[j, i]
                    if (50 < pixel[0] < 60) and (53 < pixel[1] < 63) and (95 < pixel[2] < 110):
                        points.append((j, i))
                        piece_y_max = max(i, piece_y_max)

            if not points:
                return None

            bottom_x = [x for x, y in points if y == piece_y_max]
            if not bottom_x:
                return None

            piece_x = int(sum(bottom_x) / len(bottom_x))
            piece_y = piece_y_max - self.config.piece_base_height_1_2

            # 扫描平台
            if piece_x < w / 2:
                board_x_start = piece_x
                board_x_end = w
            else:
                board_x_start = 0
                board_x_end = piece_x

            for i in range(int(h / 3), int(h * 2 / 3)):
                last_pixel = im_pixel[0, i]
                if board_x or board_y:
                    break
                board_x_sum = 0
                board_x_c = 0

                for j in range(int(board_x_start), int(board_x_end)):
                    pixel = im_pixel[j, i]
                    if abs(j - piece_x) < self.config.piece_body_width:
                        continue

                    ver_pixel = im_pixel[j, i + 5]
                    if abs(pixel[0] - last_pixel[0]) + abs(pixel[1] - last_pixel[1]) + abs(pixel[2] - last_pixel[2]) > 10 \
                            and abs(ver_pixel[0] - last_pixel[0]) + abs(ver_pixel[1] - last_pixel[1]) + abs(ver_pixel[2] - last_pixel[2]) > 10:
                        board_x_sum += j
                        board_x_c += 1
                if board_x_sum:
                    board_x = board_x_sum / board_x_c

            if not all((board_x,)):
                return None

            # 计算对称中心
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
        except Exception as e:
            print(f"图像分析失败: {e}")
            return None

    def calculate_press_time(self, distance, delta_piece_y):
        """计算按压时间"""
        try:
            scale = 0.945 * 2 / self.config.head_diameter
            actual_distance = distance * scale * (math.sqrt(6) / 2)
            press_time = (-945 + math.sqrt(945 ** 2 + 4 * 105 * 36 * actual_distance)) / (2 * 105) * 1000
            press_time *= self.config.press_coefficient
            press_time += delta_piece_y
            press_time = max(press_time, 200)
            return int(press_time)
        except:
            return 500


# ==================== Android 系统控制器 ====================
class AndroidController:
    """Android 原生操作控制器"""

    def __init__(self):
        self.screenshot_path = None
        if Android:
            try:
                self.storage_path = primary_external_storage_path()
                self.screenshot_path = os.path.join(self.storage_path, 'jump_screenshot.png')
                print(f"截图路径: {self.screenshot_path}")
            except Exception as e:
                print(f"获取存储路径失败: {e}")
                self.screenshot_path = '/sdcard/jump_screenshot.png'

    def request_permissions(self):
        """请求所需权限"""
        if Android:
            permissions = [
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ]
            request_permissions(permissions)

    def screenshot(self):
        """截取屏幕"""
        if not self.screenshot_path:
            return False

        try:
            # 使用 screencap 命令
            result = subprocess.run(
                ['screencap', '-p', self.screenshot_path],
                capture_output=True,
                timeout=10
            )

            # 等待文件写入
            time.sleep(0.5)

            if os.path.exists(self.screenshot_path):
                size = os.path.getsize(self.screenshot_path)
                print(f"截图成功，大小: {size} bytes")
                return True
            else:
                print("截图失败，文件未创建")
                return False
        except Exception as e:
            print(f"截图异常: {e}")
            return False

    def tap(self, x, y, duration_ms):
        """模拟长按触摸"""
        try:
            # 将毫秒转换为秒
            duration_sec = duration_ms / 1000.0

            # 使用 input swipe 命令模拟长按
            result = subprocess.run(
                ['input', 'swipe', str(int(x)), str(int(y)),
                 str(int(x)), str(int(y)), str(duration_sec)],
                capture_output=True,
                timeout=5
            )
            print(f"模拟按压: ({int(x)}, {int(y)}), {duration_ms}ms")
            return result.returncode == 0
        except Exception as e:
            print(f"按压失败: {e}")
            return False


# ==================== 悬浮停止按钮 ====================
class FloatingButton(FloatLayout):
    def __init__(self, stop_callback, **kwargs):
        super().__init__(**kwargs)
        self.stop_callback = stop_callback

        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 0.9)
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


# ==================== 主界面 ====================
class MainScreen(BoxLayout):
    """主设置界面"""

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
            bold=True,
            color=(0.2, 0.2, 0.2, 1)
        ))

        # 分辨率输入
        self.add_widget(Label(
            text="输入屏幕分辨率（格式：宽x高）",
            size_hint=(1, None),
            halign='left',
            font_size=16,
            color=(0.8, 0.8, 0.8, 1)
        ))

        self.resolution_input = TextInput(
            text='1080x1920',
            hint_text='如：1080x1920',
            size_hint=(1, None),
            height=50,
            multiline=False,
            font_size=18
        )
        self.add_widget(self.resolution_input)

        # 常见分辨率提示
        hints = " | ".join(COMMON_RESOLUTIONS[:4])
        self.add_widget(Label(
            text=f"常见: {hints}",
            size_hint=(1, None),
            halign='left',
            font_size=12,
            color=(0.5, 0.5, 0.5, 1)
        ))

        # 按压系数
        self.add_widget(Label(
            text="按压系数:",
            size_hint=(1, None),
            halign='left',
            font_size=16,
            color=(0.8, 0.8, 0.8, 1)
        ))

        self.coeff_slider = Slider(
            min=0.5,
            max=3.0,
            value=2.0,
            size_hint=(1, None),
            height=40
        )
        self.add_widget(self.coeff_slider)

        self.coeff_label = Label(
            text='2.00',
            size_hint=(1, None),
            height=30,
            font_size=18,
            color=(0.8, 0.8, 0.8, 1)
        )
        self.add_widget(self.coeff_label)
        self.coeff_slider.bind(value=self.on_coeff_change)

        # 开始按钮
        self.start_btn = Button(
            text='开始',
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
            text="准备就绪",
            size_hint=(1, 1),
            halign='left',
            valign='top',
            color=(0.3, 0.3, 0.3, 1)
        )
        self.add_widget(self.log_label)

    def on_coeff_change(self, slider, value):
        self.coeff_label.text = f"{value:.2f}"
        self.app.set_coefficient(value)

    def parse_resolution(self):
        """解析分辨率"""
        text = self.resolution_input.text.strip()
        try:
            if 'x' in text.lower() or 'X' in text:
                parts = text.lower().replace('x', 'X').split('X')
                if len(parts) == 2:
                    width = int(parts[0].strip())
                    height = int(parts[1].strip())
                    if width > 0 and height > 0:
                        return {'width': width, 'height': height}
        except (ValueError, IndexError):
            pass
        return None

    def start_jump(self, instance):
        """开始跳跃"""
        resolution = self.parse_resolution()

        if not resolution:
            self.show_popup("分辨率格式错误！\n请使用格式：宽x高\n例如：1080x1920")
            return

        self.app.set_resolution(resolution)

        # 切换到悬浮界面
        self.app.show_floating()

    def show_popup(self, message):
        """显示弹窗"""
        popup = Popup(
            title='提示',
            content=Label(text=message, font_size=16),
            size_hint=(0.8, 0.3)
        )
        popup.open()
        Clock.schedule_once(popup.dismiss, 2)

    def update_log(self, message):
        """更新日志"""
        self.log_label.text = message


# ==================== 主应用 ====================
class JumpApp(App):
    """微信跳一跳助手主应用"""

    def __init__(self):
        super().__init__()
        self.title = "微信跳一跳助手"

        # 配置
        self.current_resolution = None
        self.current_coefficient = 2.0
        self.is_running = False
        self.jump_count = 0

        # 核心组件
        self.config = JumpConfig()
        self.algorithm = JumpAlgorithm(self.config)
        self.controller = AndroidController()

    def build(self):
        """构建界面"""
        self.main_screen = MainScreen(self)
        return self.main_screen

    def set_resolution(self, resolution):
        """设置分辨率"""
        self.current_resolution = resolution
        print(f"分辨率设置为: {resolution['width']}x{resolution['height']}")

    def set_coefficient(self, value):
        """设置按压系数"""
        self.current_coefficient = value
        self.config.press_coefficient = value
        print(f"按压系数设置为: {value}")

    def show_floating(self):
        """显示悬浮界面"""
        if not self.controller.screenshot_path:
            self.main_screen.show_popup("权限未授予！\n请在设置中允许存储权限")
            return

        self.is_running = True
        self.jump_count = 0

        # 创建悬浮界面
        self.floating = FloatingButton(stop_callback=self.stop_jump)

        # 设置全屏悬浮
        from kivy.core.window import Window
        Window.fullscreen = True

        self.root_window = self.root
        self.root.clear_widgets()
        self.root.add_widget(self.floating)

        # 开始自动跳跃循环
        Clock.schedule_interval(self.auto_jump_loop, 1.5)

    def stop_jump(self, instance):
        """停止跳跃"""
        self.is_running = False
        Clock.unschedule(self.auto_jump_loop)

        # 恢复主界面
        from kivy.core.window import Window
        Window.fullscreen = False

        self.root.clear_widgets()
        self.root.add_widget(self.main_screen)
        self.main_screen.update_log("已停止")

    def auto_jump_loop(self, dt):
        """自动跳跃循环"""
        if not self.is_running:
            return

        try:
            # 截图
            self.floating.status_label.text = "截屏中..."
            success = self.controller.screenshot()

            if not success:
                self.floating.status_label.text = "截图失败"
                return

            # 分析
            self.floating.status_label.text = "分析中..."
            result = self.algorithm.find_piece_and_board(self.controller.screenshot_path)

            if result is None:
                self.floating.status_label.text = "检测失败"
                return

            piece_x, piece_y, board_x, board_y, delta_piece_y = result

            # 计算距离和按压时间
            distance = math.sqrt((board_x - piece_x) ** 2 + (board_y - piece_y) ** 2)
            press_time = self.algorithm.calculate_press_time(distance, delta_piece_y)

            # 执行按压
            self.controller.tap(board_x, board_y, press_time)

            # 更新状态
            self.jump_count += 1
            self.floating.status_label.text = f"距离: {distance:.0f}px | 按压: {press_time}ms | 第{self.jump_count}次"

            # 等待落地
            time.sleep(1.2)

        except Exception as e:
            self.floating.status_label.text = f"错误: {str(e)}"
            print(f"跳跃循环错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    app = JumpApp()

    # 请求权限（仅 Android）
    if Android:
        app.controller.request_permissions()

    app.run()
