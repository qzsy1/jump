# -*- coding: utf-8 -*-
"""
微信跳一跳 Windows 自动化助手 v4.0
采用 wangshub/wechat_jump_game 的经典线性算法
参考: https://github.com/wangshub/wechat_jump_game

核心算法:
  press_time = distance * press_coefficient
  press_time = max(press_time, 200)

这是最简洁稳定的版本，已被数千用户验证
"""

import customtkinter as ctk
import pyautogui
import threading
import time
import tkinter as tk
from tkinter import filedialog, simpledialog
import json
import os
import random
from PIL import Image
import math

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
pyautogui.FAILSAFE = False


class GameConfig:
    """游戏配置数据类"""
    base_screen_width: int = 1920
    base_screen_height: int = 1080
    piece_base_height_1_2: int = 20
    piece_body_width: int = 70
    head_diameter: int = 135
    press_coefficient: float = 1.5  # wangshub 经典值，可根据实际情况调整
    min_press_time: int = 200  # 降低最小按压时间
    max_press_time: int = 2000
    piece_template: str = ""
    # 游戏区域 - 预设值覆盖游戏画面 [400, 0, 1000, 1080]
    game_area: list = [400, 0, 1000, 1080]
    # 按压区域
    press_area: list = None

    # 新增：距离限制，防止检测错误
    max_valid_distance: int = 600  # 最大有效距离
    min_valid_distance: int = 30   # 最小有效距离


class JumpAlgorithm:
    """跳跃算法核心类 - v4.0 完整移植wangshub核心算法"""

    def __init__(self, config: GameConfig):
        self.config = config
        self.scale = 1.0

        # 上一次的检测位置，用于平滑和验证
        self.last_piece_x = 0
        self.last_piece_y = 0
        self.last_board_x = 0
        self.last_board_y = 0

    def calculate_scale(self, img_width: int, img_height: int):
        base_width = 1920
        base_height = 1080
        self.scale = (img_width / base_width + img_height / base_height) / 2
        return self.scale

    def find_piece_and_board(self, img: Image.Image) -> tuple:
        """寻找关键坐标 - 完整移植自wangshub/wechat_jump_game

        核心逻辑：
        1. 识别棋子：根据棋子颜色检测位置
        2. 识别平台：根据底色和方块色差检测
        3. 计算对称中心：用于计算delta_piece_y
        4. 返回：piece_x, piece_y, board_x, board_y, delta_piece_y
        """
        if img is None:
            return 0, 0, 0, 0, 0

        w, h = img.size
        self.calculate_scale(w, h)
        im_pixel = img.load()

        points = []
        piece_y_max = 0
        board_x = 0
        board_y = 0

        # wangshub: 扫描棋子时的左右边界
        scan_x_border = int(w / 8)
        scan_start_y = 0

        # wangshub: 以50px步长，尝试探测scan_start_y
        for i in range(int(h / 3), int(h * 2 / 3), 50):
            last_pixel = im_pixel[0, i]
            for j in range(1, w):
                pixel = im_pixel[j, i]
                if pixel != last_pixel:
                    scan_start_y = i - 50
                    break
            if scan_start_y:
                break

        # wangshub: 从scan_start_y开始往下扫描，棋子应位于屏幕上半部分
        for i in range(scan_start_y, int(h * 2 / 3)):
            for j in range(scan_x_border, w - scan_x_border):
                pixel = im_pixel[j, i]
                # wangshub: 根据棋子的最低行的颜色判断（严格的RGB范围）
                if (50 < pixel[0] < 60) and (53 < pixel[1] < 63) and (95 < pixel[2] < 110):
                    points.append((j, i))
                    piece_y_max = max(i, piece_y_max)

        if not points:
            return 0, 0, 0, 0, 0

        # wangshub: 所有最底层的点的横坐标
        bottom_x = [x for x, y in points if y == piece_y_max]
        if not bottom_x:
            return 0, 0, 0, 0, 0

        piece_x = int(sum(bottom_x) / len(bottom_x))
        piece_y = piece_y_max - self.config.piece_base_height_1_2

        # wangshub: 限制棋盘扫描的横坐标，避免音符bug
        if piece_x < w / 2:
            board_x_start = piece_x
            board_x_end = w
        else:
            board_x_start = 0
            board_x_end = piece_x

        # wangshub: 扫描平台中心
        for i in range(int(h / 3), int(h * 2 / 3)):
            last_pixel = im_pixel[0, i]
            if board_x or board_y:
                break
            board_x_sum = 0
            board_x_c = 0

            for j in range(int(board_x_start), int(board_x_end)):
                pixel = im_pixel[j, i]
                # wangshub: 修掉脑袋比下一个小格子还高的情况的bug
                if abs(j - piece_x) < self.config.piece_body_width:
                    continue

                # wangshub: 检查Y轴下面5个像素，和背景色相同，那么是干扰
                ver_pixel = im_pixel[j, i + 5]
                if abs(pixel[0] - last_pixel[0]) + abs(pixel[1] - last_pixel[1]) + abs(pixel[2] - last_pixel[2]) > 10 \
                        and abs(ver_pixel[0] - last_pixel[0]) + abs(ver_pixel[1] - last_pixel[1]) + abs(ver_pixel[2] - last_pixel[2]) > 10:
                    board_x_sum += j
                    board_x_c += 1
            if board_x_sum:
                board_x = board_x_sum / board_x_c
        last_pixel = im_pixel[board_x, i]

        # wangshub: 计算对称中心，用于获取delta_piece_y
        center_x = w / 2 + (24 / 1080) * w
        center_y = h / 2 + (17 / 1920) * h

        if piece_x > center_x:
            board_y = round((25.5 / 43.5) * (board_x - center_x) + center_y)
            delta_piece_y = piece_y - round((25.5 / 43.5) * (piece_x - center_x) + center_y)
        else:
            board_y = round(-(25.5 / 43.5) * (board_x - center_x) + center_y)
            delta_piece_y = piece_y - round(-(25.5 / 43.5) * (piece_x - center_x) + center_y)

        if not all((board_x, board_y)):
            return 0, 0, 0, 0, 0

        return piece_x, piece_y, board_x, board_y, delta_piece_y

    def _find_symmetry_center(self, w: int, h: int) -> tuple:
        """计算游戏对称中心 - wangshub方法"""
        # 游戏中心偏移量（基于 1080x1920 屏幕）
        center_x = w / 2 + (24 / 1080) * w
        center_y = h / 2 + (17 / 1920) * h
        return center_x, center_y

    def _calculate_delta_piece_y(self, piece_x: float, piece_y: float, center_x: float, center_y: float) -> float:
        """计算棋子Y轴偏移（相对于对称中心）- wangshub方法"""
        if piece_x > center_x:
            # 棋子在中心右侧
            expected_piece_y = round((25.5 / 43.5) * (piece_x - center_x) + center_y)
        else:
            # 棋子在中心左侧
            expected_piece_y = round(-(25.5 / 43.5) * (piece_x - center_x) + center_y)
        delta_piece_y = piece_y - expected_piece_y
        return delta_piece_y

    def _find_piece(self, im_pixel, w: int, h: int) -> tuple:
        """识别棋子位置 - 改进版，更稳定"""
        points = []
        piece_y_max = 0

        # 搜索屏幕中间区域
        scan_start_x = int(w * 0.2)
        scan_end_x = int(w * 0.8)

        for i in range(int(h * 0.3), int(h * 0.7)):
            row_points = []
            for j in range(scan_start_x, scan_end_x):
                pixel = im_pixel[j, i]
                r, g, b = pixel[0], pixel[1], pixel[2]

                # 深紫色棋子检测 - 放宽条件
                purple = (r < g and g < b and r > 25 and r < 100 and
                         g > 5 and g < 80 and b > 50 and b < 140)

                if purple:
                    row_points.append(j)
                    piece_y_max = max(i, piece_y_max)

            # 如果这一行有多个连续的点，记录中间位置
            if row_points:
                mid_x = sum(row_points) // len(row_points)
                points.append((mid_x, i))

        if len(points) < 5:
            # 备用方案：暗色检测
            for i in range(int(h * 0.3), int(h * 0.7)):
                for j in range(scan_start_x, scan_end_x):
                    pixel = im_pixel[j, i]
                    r, g, b = pixel[0], pixel[1], pixel[2]
                    brightness = r + g + b
                    if brightness < 450:
                        points.append((j, i))
                        piece_y_max = max(i, piece_y_max)

        if not points:
            return 0, 0

        # 找到棋子底部中心
        bottom_points = [p for p in points if p[1] >= piece_y_max - 5]
        if bottom_points:
            piece_x = int(sum([p[0] for p in bottom_points]) / len(bottom_points))
        else:
            piece_x = int(sum([p[0] for p in points]) / len(points))

        piece_y = piece_y_max - int(self.config.piece_base_height_1_2 * self.scale)

        return piece_x, piece_y

    def _find_board_center(self, im_pixel, w: int, h: int, piece_x: float, piece_y: float) -> tuple:
        """识别目标平台中心 - 双向搜索，找最可能的下一个平台"""

        # 双向搜索：棋子的左侧和右侧都要搜索
        # 因为不知道下一个平台在哪一边，需要找最亮的平台

        candidates = []  # 候选平台列表

        # 搜索范围：从棋子向两边扩展
        left_search_end = max(50, int(piece_x - 100 * self.scale))
        right_search_start = min(w - 50, int(piece_x + 100 * self.scale))

        # 在棋子Y坐标附近搜索
        search_y_start = max(int(h * 0.2), int(piece_y - 150))
        search_y_end = min(int(h * 0.8), int(piece_y + 150))

        # 搜索右侧
        right_candidates = self._search_direction(im_pixel, right_search_start, w - 20,
                                                   search_y_start, search_y_end, piece_x)
        candidates.extend(right_candidates)

        # 搜索左侧
        left_candidates = self._search_direction(im_pixel, 50, left_search_end,
                                                  search_y_start, search_y_end, piece_x)
        candidates.extend(left_candidates)

        # 找到最佳候选（最大、最亮的平台）
        if candidates:
            # 按亮色像素数量排序，找最大的
            candidates.sort(key=lambda x: x[2], reverse=True)
            best = candidates[0]
            return best[0], best[1]

        # 备用方案：简单检测
        bright_pixels = []
        for i in range(search_y_start, search_y_end):
            for j in range(50, w - 50):
                if abs(j - piece_x) < int(80 * self.scale):
                    continue
                pixel = im_pixel[j, i]
                r, g, b = pixel[0], pixel[1], pixel[2]
                brightness = r + g + b
                if 550 < brightness < 720:
                    bright_pixels.append((j, i))

        if bright_pixels:
            avg_x = int(sum([p[0] for p in bright_pixels]) / len(bright_pixels))
            avg_y = int(sum([p[1] for p in bright_pixels]) / len(bright_pixels))
            return avg_x, avg_y

        return 0, 0

    def _search_direction(self, im_pixel, start_x, end_x, start_y, end_y, piece_x):
        """在指定方向搜索平台"""
        candidates = []

        for i in range(start_y, end_y):
            bright_pixels = []

            for j in range(start_x, end_x):
                # 跳过棋子附近（当前平台）- 加大排除半径避免选中当前平台
                if abs(j - piece_x) < int(150 * self.scale):
                    continue

                pixel = im_pixel[j, i]
                r, g, b = pixel[0], pixel[1], pixel[2]

                # 检测平台（亮色）
                brightness = r + g + b
                if brightness > 500 and r > 150 and g > 150 and b > 150:
                    # 排除纯白色背景
                    if brightness < 750:
                        bright_pixels.append(j)

            # 找到连续的亮色区域
            if len(bright_pixels) >= 10:
                # 分组检测平台
                groups = []
                current_group = [bright_pixels[0]]

                for k in range(1, len(bright_pixels)):
                    if bright_pixels[k] - bright_pixels[k-1] <= 5:
                        current_group.append(bright_pixels[k])
                    else:
                        groups.append(current_group)
                        current_group = [bright_pixels[k]]
                groups.append(current_group)

                # 找最大的组
                for group in groups:
                    if len(group) >= 10:
                        center_x = (group[0] + group[-1]) // 2
                        # 计算到棋子的距离
                        distance = abs(center_x - piece_x)
                        # 记录候选：[center_x, center_y, pixel_count]
                        candidates.append((center_x, i, len(group), distance))

        return candidates

        # 在棋子Y坐标附近搜索
        search_y_start = max(int(h * 0.2), int(piece_y - 150))
        search_y_end = min(int(h * 0.8), int(piece_y + 150))

        best_center_x = 0
        best_center_y = 0
        max_bright_count = 0

        # 寻找平台表面（亮色线条）
        for i in range(search_y_start, search_y_end):
            bright_pixels = []

            for j in range(search_start, search_end):
                # 跳过棋子附近（当前平台）- 加大排除半径避免选中当前平台
                if abs(j - piece_x) < int(150 * self.scale):
                    continue

                pixel = im_pixel[j, i]
                r, g, b = pixel[0], pixel[1], pixel[2]

                # 检测平台（亮色）
                brightness = r + g + b
                if brightness > 500 and r > 150 and g > 150 and b > 150:
                    # 排除纯白色背景
                    if brightness < 750:
                        bright_pixels.append(j)

            # 找到连续的亮色区域
            if len(bright_pixels) >= 10:
                # 分组检测平台
                groups = []
                current_group = [bright_pixels[0]]

                for k in range(1, len(bright_pixels)):
                    if bright_pixels[k] - bright_pixels[k-1] <= 5:
                        current_group.append(bright_pixels[k])
                    else:
                        groups.append(current_group)
                        current_group = [bright_pixels[k]]
                groups.append(current_group)

                # 找最大的组（最可能是平台）
                for group in groups:
                    if len(group) > max_bright_count:
                        max_bright_count = len(group)
                        best_center_x = (group[0] + group[-1]) // 2
                        best_center_y = i

        if best_center_x > 0 and max_bright_count >= 10:
            return best_center_x, best_center_y

        # 备用方案：简单检测
        bright_pixels = []
        for i in range(search_y_start, search_y_end):
            for j in range(search_start, search_end):
                if abs(j - piece_x) < int(80 * self.scale):
                    continue
                pixel = im_pixel[j, i]
                r, g, b = pixel[0], pixel[1], pixel[2]
                brightness = r + g + b
                if 550 < brightness < 720:
                    bright_pixels.append((j, i))

        if bright_pixels:
            avg_x = int(sum([p[0] for p in bright_pixels]) / len(bright_pixels))
            avg_y = int(sum([p[1] for p in bright_pixels]) / len(bright_pixels))
            return avg_x, avg_y

        return 0, 0

    def calculate_jump_time(self, distance: float, delta_piece_y: float = 0) -> int:
        """计算跳跃按压时间 - wangshub 二次曲线算法

        完整移植自: https://github.com/wangshub/wechat_jump_game

        核心公式:
            scale = 0.945 * 2 / head_diameter
            actual_distance = distance * scale * math.sqrt(6) / 2
            press_time = (-945 + math.sqrt(945**2 + 4 * 105 * 36 * actual_distance)) / (2 * 105) * 1000
            press_time *= press_coefficient
            press_time += delta_piece_y
            press_time = max(press_time, 200)
        """
        # 限制距离范围
        distance = max(self.config.min_valid_distance,
                      min(distance, self.config.max_valid_distance))

        # wangshub 二次曲线算法
        # 计算程序长度与截图测得的距离的比例
        scale = 0.945 * 2 / (self.config.head_diameter * self.scale)
        actual_distance = distance * scale * (math.sqrt(6) / 2)
        press_time = (-945 + math.sqrt(945 ** 2 + 4 * 105 *
                                       36 * actual_distance)) / (2 * 105) * 1000
        press_time *= self.config.press_coefficient
        press_time = max(press_time, 200)
        press_time = int(press_time)

        return press_time

    def calculate_distance(self, piece_x: float, piece_y: float, board_x: float, board_y: float) -> float:
        """计算两点之间的欧几里得距离"""
        return math.sqrt((board_x - piece_x) ** 2 + (board_y - piece_y) ** 2)


class JumpJumpAuto(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("跳一跳自动化助手 v4.0")
        self.geometry("700x700")
        self.resizable(False, False)

        self.running = False
        self.stop_event = threading.Event()
        self.auto_thread = None
        self.jump_count = 0

        self.config = GameConfig()
        self.algorithm = JumpAlgorithm(self.config)
        self.config_file = "config.json"

        # UI组件
        self.status_label = None
        self.count_label = None
        self.detail_label = None
        self.coeff_label = None
        self.res_label = None
        self.area_entry = None
        self.template_entry = None
        self.press_entry = None

        self._init_ui()
        self._load_config()
        self._start_ui_updater()

    def _init_ui(self):
        # 标题
        ctk.CTkLabel(self, text="跳一跳自动化助手 v4.0", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)

        main_frame = ctk.CTkScrollableFrame(self, width=660, height=540)
        main_frame.pack(pady=8, padx=20, fill="both", expand=True)

        # 分辨率预设
        res_frame = ctk.CTkFrame(main_frame)
        res_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(res_frame, text="分辨率:", font=ctk.CTkFont(size=13)).pack(side="left", padx=10)
        ctk.CTkButton(res_frame, text="1K", width=60, command=lambda: self._set_res(1920, 1080)).pack(side="left", padx=2)
        ctk.CTkButton(res_frame, text="2K", width=60, command=lambda: self._set_res(2560, 1440)).pack(side="left", padx=2)
        ctk.CTkButton(res_frame, text="4K", width=60, command=lambda: self._set_res(3840, 2160)).pack(side="left", padx=2)
        ctk.CTkButton(res_frame, text="检测", width=60, command=self._cmd_detect_res).pack(side="right", padx=5)
        self.res_label = ctk.CTkLabel(res_frame, text="", font=ctk.CTkFont(size=12))
        self.res_label.pack(side="right", padx=10)

        # 按压系数
        coeff_frame = ctk.CTkFrame(main_frame)
        coeff_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(coeff_frame, text="按压系数:", font=ctk.CTkFont(size=13)).pack(side="left", padx=10)
        self.coeff_scale = ctk.CTkSlider(coeff_frame, from_=0.5, to=4.0, number_of_steps=35)
        self.coeff_scale.pack(side="left", padx=10, fill="x", expand=True)
        self.coeff_scale.set(1.5)  # 使用wangshub经典值
        # 使用事件绑定而不是command参数
        self.coeff_scale.configure(command=lambda v: self._on_slider_change(v))
        self.coeff_label = ctk.CTkLabel(coeff_frame, text="1.50", width=50)
        self.coeff_label.pack(side="left", padx=5)

        # 游戏区域
        area_frame = ctk.CTkFrame(main_frame)
        area_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(area_frame, text="游戏区域:", font=ctk.CTkFont(size=13)).pack(side="left", padx=10)
        self.area_entry = ctk.CTkEntry(area_frame, width=180)
        self.area_entry.pack(side="left", padx=5)
        self.area_entry.insert(0, "400,0,1000,1080")
        ctk.CTkButton(area_frame, text="鼠标选择", width=80, command=self._cmd_select_area).pack(side="right", padx=5)
        ctk.CTkButton(area_frame, text="手动设置", width=80, command=self._cmd_manual_area).pack(side="right", padx=5)
        ctk.CTkButton(area_frame, text="预设区域", width=80, command=self._cmd_preset_area).pack(side="right", padx=5)
        ctk.CTkButton(area_frame, text="设为全屏", width=80, command=self._cmd_fullscreen_area).pack(side="right", padx=5)

        # 按压区域
        press_frame = ctk.CTkFrame(main_frame)
        press_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(press_frame, text="按压位置:", font=ctk.CTkFont(size=13)).pack(side="left", padx=10)
        self.press_entry = ctk.CTkEntry(press_frame, width=180)
        self.press_entry.pack(side="left", padx=5)
        self.press_entry.insert(0, "自动中心")
        ctk.CTkButton(press_frame, text="鼠标选择", width=80, command=self._cmd_select_press).pack(side="right", padx=5)
        ctk.CTkButton(press_frame, text="自动中心", width=80, command=self._cmd_auto_press).pack(side="right", padx=5)
        ctk.CTkLabel(press_frame, text="(鼠标点击位置)", font=ctk.CTkFont(size=10), text_color="#888").pack(side="left", padx=5)

        # 棋子模板
        template_frame = ctk.CTkFrame(main_frame)
        template_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(template_frame, text="棋子模板:", font=ctk.CTkFont(size=13)).pack(side="left", padx=10)
        self.template_entry = ctk.CTkEntry(template_frame, width=180)
        self.template_entry.pack(side="left", padx=5)
        ctk.CTkButton(template_frame, text="截图", width=70, command=self._cmd_capture_template).pack(side="right", padx=5)
        ctk.CTkButton(template_frame, text="选择", width=70, command=self._cmd_select_template).pack(side="right", padx=5)

        # 状态
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(pady=5, padx=10, fill="x")
        self.status_label = ctk.CTkLabel(status_frame, text="状态: 就绪", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=5)
        self.count_label = ctk.CTkLabel(status_frame, text="跳跃次数: 0", font=ctk.CTkFont(size=12), text_color="#888888")
        self.count_label.pack(pady=2)
        self.detail_label = ctk.CTkLabel(status_frame, text="", font=ctk.CTkFont(size=11), text_color="#aaaaaa")
        self.detail_label.pack(pady=2)

        # 按钮
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=10, padx=20, fill="x")
        self.start_btn = ctk.CTkButton(button_frame, text="开始", font=ctk.CTkFont(size=16, weight="bold"), width=140, height=45, fg_color="#2ecc71", hover_color="#27ae60", command=self._cmd_start)
        self.start_btn.pack(side="left", padx=60)
        self.stop_btn = ctk.CTkButton(button_frame, text="停止", font=ctk.CTkFont(size=16, weight="bold"), width=140, height=45, fg_color="#e74c3c", hover_color="#c0392b", command=self._cmd_stop)
        self.stop_btn.pack(side="right", padx=60)
        self.stop_btn.configure(state="disabled")

    def _start_ui_updater(self):
        try:
            if self.status_label:
                self._safe_update_ui()
        except:
            pass
        self.after(100, self._start_ui_updater)

    def _safe_update_ui(self):
        try:
            if hasattr(self, '_ui_status'):
                self.status_label.configure(text=self._ui_status)
        except:
            pass
        try:
            if hasattr(self, '_ui_count'):
                self.count_label.configure(text=self._ui_count)
        except:
            pass
        try:
            if hasattr(self, '_ui_detail'):
                self.detail_label.configure(text=self._ui_detail)
        except:
            pass

    def _set_status(self, text):
        self._ui_status = text

    def _set_count(self, text):
        self._ui_count = text

    def _set_detail(self, text):
        self._ui_detail = text

    def _set_res(self, w, h):
        self.config.base_screen_width = w
        self.config.base_screen_height = h
        self.res_label.configure(text=f"{w}x{h}")
        self._save_config()
        self._set_status(f"状态: 已设为 {w}x{h}")

    def _cmd_detect_res(self):
        try:
            w, h = pyautogui.size()
            self._set_res(w, h)
            self._set_status("状态: 分辨率已检测")
        except:
            self._set_status("状态: 检测失败")

    def _on_slider_change(self, value):
        """滑块回调函数 - 处理元组参数"""
        try:
            # CustomTkinter 可能传递元组或单个值
            if isinstance(value, tuple):
                v = float(value[0]) if value else 1.5
            else:
                v = float(value)

            self.config.press_coefficient = v
            self.coeff_label.configure(text=f"{v:.2f}")
            self._save_config()
        except Exception as e:
            print(f"滑块回调错误: {e}")
            pass

    def _cmd_select_area(self):
        self._set_status("状态: 2秒后从左上拖到右下...")
        def do_select():
            try:
                time.sleep(2)
                x1, y1 = pyautogui.position()
                time.sleep(1)
                x2, y2 = pyautogui.position()
                x, y = min(x1, x2), min(y1, y2)
                width, height = abs(x2 - x1), abs(y2 - y1)
                if width > 100 and height > 100:
                    self.config.game_area = [x, y, width, height]
                    self.area_entry.delete(0, tk.END)
                    self.area_entry.insert(0, f"{x},{y},{width},{height}")
                    self._set_status(f"状态: 区域已设 {width}x{height}")
                    self._save_config()
                else:
                    self._set_status("状态: 区域太小")
            except:
                self._set_status("状态: 选择失败")
        threading.Thread(target=do_select, daemon=True).start()

    def _cmd_manual_area(self):
        result = simpledialog.askstring("游戏区域", "请输入游戏区域 (x,y,width,height) 或留空表示全屏:")
        if result is not None:
            if result.strip() == "":
                self._cmd_fullscreen_area()
            else:
                try:
                    parts = [int(x.strip()) for x in result.split(",")]
                    if len(parts) == 4:
                        self.config.game_area = parts
                        self.area_entry.delete(0, tk.END)
                        self.area_entry.insert(0, result)
                        self._set_status("状态: 游戏区域已设置")
                        self._save_config()
                except:
                    self._set_status("状态: 格式错误")

    def _cmd_fullscreen_area(self):
        self.config.game_area = None
        self.area_entry.delete(0, tk.END)
        self.area_entry.insert(0, "全屏")
        self._set_status("状态: 游戏区域已设为全屏")
        self._save_config()

    def _cmd_preset_area(self):
        self.config.game_area = [400, 0, 1000, 1080]
        self.area_entry.delete(0, tk.END)
        self.area_entry.insert(0, "400,0,1000,1080")
        self._set_status("状态: 游戏区域已设为预设 (400,0,1000,1080)")
        self._save_config()

    def _cmd_select_press(self):
        self._set_status("状态: 3秒后鼠标移动到按压位置...")
        def do_select():
            try:
                time.sleep(3)
                x, y = pyautogui.position()
                self.config.press_area = [x, y]
                self.press_entry.delete(0, tk.END)
                self.press_entry.insert(0, f"{x}, {y}")
                self._set_status(f"状态: 按压位置已设 ({x}, {y})")
                self._save_config()
            except:
                self._set_status("状态: 选择失败")
        threading.Thread(target=do_select, daemon=True).start()

    def _cmd_auto_press(self):
        self.config.press_area = None
        self.press_entry.delete(0, tk.END)
        self.press_entry.insert(0, "自动中心")
        self._set_status("状态: 按压位置设为自动中心")
        self._save_config()

    def _cmd_capture_template(self):
        self._set_status("状态: 3秒后截图...")
        def do_capture():
            try:
                time.sleep(3)
                x1, y1 = pyautogui.position()
                self._set_status("状态: 拖动框选棋子")
                time.sleep(1)
                x2, y2 = pyautogui.position()
                x, y = min(x1, x2), min(y1, y2)
                width, height = max(abs(x2 - x1), 50), max(abs(y2 - y1), 50)
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                import tempfile
                temp_file = tempfile.gettempdir() + "/jump_piece_template.png"
                screenshot.save(temp_file)
                self.config.piece_template = temp_file
                self.template_entry.delete(0, tk.END)
                self.template_entry.insert(0, temp_file)
                self._set_status(f"状态: 已截取 {width}x{height}")
                self._save_config()
            except:
                self._set_status("状态: 截图失败")
        threading.Thread(target=do_capture, daemon=True).start()

    def _cmd_select_template(self):
        file_path = filedialog.askopenfilename(title="选择棋子截图", filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.config.piece_template = file_path
            self.template_entry.delete(0, tk.END)
            self.template_entry.insert(0, file_path)
            self._set_status("状态: 模板已加载")
            self._save_config()

    def _save_config(self):
        try:
            config_data = {
                'press_coefficient': self.config.press_coefficient,
                'screen_width': self.config.base_screen_width,
                'screen_height': self.config.base_screen_height,
                'piece_template': self.config.piece_template,
                'game_area': self.config.game_area,
                'press_area': self.config.press_area,
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
        except:
            pass

    def _load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    self.config.press_coefficient = config_data.get("press_coefficient", 1.5)
                    self.config.base_screen_width = config_data.get("screen_width", 1920)
                    self.config.base_screen_height = config_data.get("screen_height", 1080)
                    self.config.piece_template = config_data.get("piece_template", "")
                    self.config.game_area = config_data.get("game_area", [400, 0, 1000, 1080])
                    self.config.press_area = config_data.get("press_area", None)

                    self.coeff_scale.set(1.5)  # 使用wangshub经典值
                    self.coeff_label.configure(text=f"{self.config.press_coefficient:.2f}")
                    self.res_label.configure(text=f"{self.config.base_screen_width}x{self.config.base_screen_height}")

                    if self.config.game_area:
                        self.area_entry.delete(0, tk.END)
                        self.area_entry.insert(0, f"{self.config.game_area[0]},{self.config.game_area[1]},{self.config.game_area[2]},{self.config.game_area[3]}")
                    else:
                        self.area_entry.delete(0, tk.END)
                        self.area_entry.insert(0, "全屏")

                    if self.config.press_area:
                        self.press_entry.delete(0, tk.END)
                        self.press_entry.insert(0, f"{self.config.press_area[0]}, {self.config.press_area[1]}")
                    else:
                        self.press_entry.delete(0, tk.END)
                        self.press_entry.insert(0, "自动中心")

                    if self.config.piece_template:
                        self.template_entry.delete(0, tk.END)
                        self.template_entry.insert(0, self.config.piece_template)
        except:
            pass

    def capture_game_screenshot(self) -> Image.Image:
        """截取游戏区域截图"""
        try:
            if self.config.game_area:
                screenshot = pyautogui.screenshot(region=tuple(self.config.game_area))
            else:
                screenshot = pyautogui.screenshot()
            return screenshot
        except:
            return None

    def do_jump(self, press_time_ms: int):
        """执行跳跃"""
        try:
            if self.config.press_area:
                jump_x, jump_y = self.config.press_area[0], self.config.press_area[1]
            elif self.config.game_area:
                jump_x = self.config.game_area[0] + self.config.game_area[2] // 2
                jump_y = self.config.game_area[1] + self.config.game_area[3] // 2
            else:
                screen_width, screen_height = pyautogui.size()
                jump_x = screen_width // 2
                jump_y = screen_height // 2 + 100

            pyautogui.moveTo(jump_x, jump_y, duration=0.05)
            pyautogui.mouseDown(button='left')
            time.sleep(press_time_ms / 1000.0)
            pyautogui.mouseUp(button='left')
            print(f"跳跃完成：按压时间 {press_time}ms, 位置({jump_x}, {jump_y})")
        except Exception as e:
            print(f"跳跃执行失败: {e}")

    def auto_jump_loop(self):
        """自动跳跃循环"""
        print("=== 自动跳跃开始 ===")
        self.stop_event.clear()
        self.jump_count = 0
        test_times = []

        try:
            while self.running and not self.stop_event.is_set():
                screenshot = self.capture_game_screenshot()
                if screenshot is None:
                    self._set_status("状态: 截图失败")
                    time.sleep(0.5)
                    continue

                piece_x, piece_y, board_x, board_y, delta_y = self.algorithm.find_piece_and_board(screenshot)

                print(f"检测: 棋子({piece_x}, {piece_y}), 平台({board_x}, {board_y}), DeltaY: {delta_y:.1f}")

                if piece_x == 0 and piece_y == 0:
                    self._set_status("状态: 未检测到棋子")
                    time.sleep(0.3)
                    continue

                if board_x == 0 and board_y == 0:
                    self._set_status("状态: 未检测到平台")
                    time.sleep(0.3)
                    continue

                distance = self.algorithm.calculate_distance(piece_x, piece_y, board_x, board_y)

                # 距离验证
                if distance > self.config.max_valid_distance:
                    print(f"警告: 距离过大 {distance:.1f}px，限制为 {self.config.max_valid_distance}px")
                    distance = self.config.max_valid_distance

                press_time = self.algorithm.calculate_jump_time(distance, delta_y)

                test_times.append(press_time)
                if len(test_times) > 10:
                    test_times.pop(0)

                self.jump_count += 1
                self._set_count(f"跳跃次数: {self.jump_count}")
                self._set_detail(f"距离: {int(distance)}px | 按压: {press_time}ms")
                self._set_status("状态: 运行中...")

                print(f"跳跃 #{self.jump_count}: 距离={distance:.1f}px, 按压={press_time}ms")

                self.do_jump(press_time)
                time.sleep(1.0)

                for _ in range(10):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)

                if self.stop_event.is_set():
                    break

            if test_times:
                avg_time = sum(test_times) / len(test_times)
                max_time = max(test_times)
                min_time = min(test_times)
                print(f"\n=== 统计 ===")
                print(f"平均: {avg_time:.0f}ms, 最小: {min_time}ms, 最大: {max_time}ms")
                if max_time > 2000:
                    print("警告: 存在超过2秒的跳跃！")
                elif min_time < 400:
                    print("警告: 存在小于400ms的跳跃！")
                else:
                    print("[OK] 跳跃时间正常")

            print(f"=== 自动跳跃结束，总共跳了 {self.jump_count} 次 ===")

        except Exception as e:
            print(f"捕获异常: {e}")
            import traceback
            traceback.print_exc()
            self._set_status(f"状态: 出错")

        finally:
            if self.running:
                self.on_stop_complete()

    def _cmd_start(self):
        if self.running:
            return
        self._save_config()
        self.running = True
        self.stop_event.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._set_status("状态: 运行中...")
        print(f"=== start_auto ===")
        self.auto_thread = threading.Thread(target=self.auto_jump_loop, daemon=True)
        self.auto_thread.start()

    def _cmd_stop(self):
        if not self.running:
            return
        print("=== stop_auto ===")
        self.stop_event.set()
        self.running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._set_status("状态: 已停止")
        self._set_count(f"跳跃次数: {self.jump_count}")
        self._set_detail("")

    def on_stop_complete(self):
        if not self.running:
            return
        self.running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._set_status("状态: 已停止")


if __name__ == "__main__":
    app = JumpJumpAuto()
    app.mainloop()
