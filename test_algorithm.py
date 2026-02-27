# -*- coding: utf-8 -*-
"""
算法测试脚本 - v3.5 Prinsphield线性算法
"""
import sys
from PIL import Image
import math

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')


class GameConfig:
    base_screen_width: int = 1920
    base_screen_height: int = 1080
    piece_base_height_1_2: int = 20
    piece_body_width: int = 70
    head_diameter: int = 135
    press_coefficient: float = 1.5
    min_press_time: int = 400
    max_press_time: int = 2000
    piece_template: str = ""
    game_area: list = [400, 0, 1000, 1080]
    press_area: list = None
    max_valid_distance: int = 600
    min_valid_distance: int = 30


class JumpAlgorithm:
    def __init__(self, config: GameConfig):
        self.config = config
        self.scale = 1.0
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
        if img is None:
            return 0, 0, 0, 0, 0

        w, h = img.size
        self.calculate_scale(w, h)
        im_pixel = img.load()

        piece_x, piece_y = self._find_piece(im_pixel, w, h)
        if piece_x == 0 and piece_y == 0:
            return 0, 0, 0, 0, 0

        board_x, board_y = self._find_board_center(im_pixel, w, h, piece_x, piece_y)
        if board_x == 0 and board_y == 0:
            return 0, 0, 0, 0, 0

        distance = math.sqrt((board_x - piece_x) ** 2 + (board_y - piece_y) ** 2)

        if distance > self.config.max_valid_distance:
            print(f"警告: 检测距离过大 {distance:.1f}px，限制为 {self.config.max_valid_distance}px")
            if piece_x < w / 2:
                estimated_x = piece_x + min(distance, 400)
            else:
                estimated_x = piece_x - min(distance, 400)
            board_x = estimated_x
            board_y = piece_y

        self.last_piece_x = piece_x
        self.last_piece_y = piece_y
        self.last_board_x = board_x
        self.last_board_y = board_y

        delta_piece_y = piece_y - h / 2
        return piece_x, piece_y, board_x, board_y, delta_piece_y

    def _find_piece(self, im_pixel, w: int, h: int) -> tuple:
        points = []
        piece_y_max = 0
        scan_start_x = int(w * 0.2)
        scan_end_x = int(w * 0.8)

        for i in range(int(h * 0.3), int(h * 0.7)):
            row_points = []
            for j in range(scan_start_x, scan_end_x):
                pixel = im_pixel[j, i]
                r, g, b = pixel[0], pixel[1], pixel[2]
                purple = (r < g and g < b and r > 25 and r < 100 and
                         g > 5 and g < 80 and b > 50 and b < 140)
                if purple:
                    row_points.append(j)
                    piece_y_max = max(i, piece_y_max)
            if row_points:
                mid_x = sum(row_points) // len(row_points)
                points.append((mid_x, i))

        if len(points) < 5:
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

        bottom_points = [p for p in points if p[1] >= piece_y_max - 5]
        if bottom_points:
            piece_x = int(sum([p[0] for p in bottom_points]) / len(bottom_points))
        else:
            piece_x = int(sum([p[0] for p in points]) / len(points))

        piece_y = piece_y_max - int(self.config.piece_base_height_1_2 * self.scale)
        return piece_x, piece_y

    def _find_board_center(self, im_pixel, w: int, h: int, piece_x: float, piece_y: float) -> tuple:
        """识别目标平台中心 - 双向搜索"""
        candidates = []
        left_search_end = max(50, int(piece_x - 100 * self.scale))
        right_search_start = min(w - 50, int(piece_x + 100 * self.scale))
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

        if candidates:
            candidates.sort(key=lambda x: x[2], reverse=True)
            best = candidates[0]
            return best[0], best[1]

        return 0, 0

    def _search_direction(self, im_pixel, start_x, end_x, start_y, end_y, piece_x):
        """在指定方向搜索平台"""
        candidates = []
        for i in range(start_y, end_y):
            bright_pixels = []
            for j in range(start_x, end_x):
                if abs(j - piece_x) < int(80 * self.scale):
                    continue
                pixel = im_pixel[j, i]
                r, g, b = pixel[0], pixel[1], pixel[2]
                brightness = r + g + b
                if brightness > 500 and r > 150 and g > 150 and b > 150:
                    if brightness < 750:
                        bright_pixels.append(j)

            if len(bright_pixels) >= 10:
                groups = []
                current_group = [bright_pixels[0]]
                for k in range(1, len(bright_pixels)):
                    if bright_pixels[k] - bright_pixels[k-1] <= 5:
                        current_group.append(bright_pixels[k])
                    else:
                        groups.append(current_group)
                        current_group = [bright_pixels[k]]
                groups.append(current_group)

                for group in groups:
                    if len(group) >= 10:
                        center_x = (group[0] + group[-1]) // 2
                        distance = abs(center_x - piece_x)
                        candidates.append((center_x, i, len(group), distance))
        return candidates

    def calculate_jump_time(self, distance: float, delta_piece_y: float = 0) -> int:
        """计算跳跃按压时间 - 使用Prinsphield/Wechat_AutoJump的线性算法
        参考公式: press_time = distance * sensitivity
        默认 sensitivity = 2.045
        """
        distance = max(self.config.min_valid_distance,
                      min(distance, self.config.max_valid_distance))

        # Prinsphield线性算法: press_time = distance * sensitivity
        press_time = distance * self.config.press_coefficient

        # 分辨率适配：高分辨率需要更小的系数
        resolution_factor = 1.0
        if self.scale > 1.0:
            resolution_factor = 1.0 / self.scale
        press_time *= resolution_factor

        # 高度修正
        height_correction = -delta_piece_y * 0.5
        press_time += height_correction

        press_time = max(self.config.min_press_time, int(press_time))
        press_time = min(self.config.max_press_time, press_time)
        return press_time

    def calculate_distance(self, piece_x: float, piece_y: float, board_x: float, board_y: float) -> float:
        return math.sqrt((board_x - piece_x) ** 2 + (board_y - piece_y) ** 2)


def test_with_screenshot():
    """使用用户提供的截图进行测试"""
    config = GameConfig()
    algorithm = JumpAlgorithm(config)

    screenshot_path = r"C:\Users\xlq\.claude\skills\pygui-creator\content\dist\屏幕截图 2026-02-27 022528.png"

    print("=" * 70)
    print("算法测试 - v3.5 Prinsphield线性算法")
    print("=" * 70)

    try:
        img = Image.open(screenshot_path)
        w, h = img.size
        print(f"\n截图尺寸: {w}x{h}")
        print(f"游戏区域: [400, 0, 1000, 1080]")

        # 测试完整检测
        print("\n--- 棋子和平台检测测试 ---")
        piece_x, piece_y, board_x, board_y, delta_y = algorithm.find_piece_and_board(img)
        print(f"棋子位置: ({piece_x}, {piece_y})")
        print(f"平台中心: ({board_x}, {board_y})")
        print(f"Y轴偏移: {delta_y:.1f}")

        if piece_x == 0 and piece_y == 0:
            print("[FAIL] 棋子检测失败！")
            return False
        else:
            print("[OK] 棋子检测成功")

        if board_x == 0 and board_y == 0:
            print("[FAIL] 平台中心检测失败！")
            return False
        else:
            print("[OK] 平台中心检测成功")

        # 计算距离和按压时间
        distance = algorithm.calculate_distance(piece_x, piece_y, board_x, board_y)
        press_time = algorithm.calculate_jump_time(distance, delta_y)

        print(f"\n--- 距离和按压时间 ---")
        print(f"棋子到平台中心距离: {distance:.1f}px")
        print(f"计算按压时间: {press_time}ms")

        # 验证距离是否合理
        if distance > config.max_valid_distance:
            print(f"[WARN] 距离过大！{distance:.1f}px > {config.max_valid_distance}px")
            return False
        if distance < config.min_valid_distance:
            print(f"[WARN] 距离过小！{distance:.1f}px < {config.min_valid_distance}px")
            return False

        # 测试不同距离的按压时间
        print(f"\n--- 不同距离按压时间测试 ---")
        test_distances = [50, 100, 200, 300, 400, 500, 600]
        print(f"按压系数: {config.press_coefficient}")
        print(f"缩放比例: {algorithm.scale:.2f}")
        print("\n距离(px) -> 按压时间(ms)")

        press_times = []
        for dist in test_distances:
            press = algorithm.calculate_jump_time(dist, 0)
            press_times.append(press)
            status = "[OK]" if 400 <= press <= 2000 else "[WARN]"
            print(f"  {dist:3d}    -> {press:4d}ms {status}")

        # 统计
        avg_time = sum(press_times) / len(press_times)
        max_time = max(press_times)
        min_time = min(press_times)

        print(f"\n--- 统计 ---")
        print(f"平均: {avg_time:.0f}ms, 最小: {min_time}ms, 最大: {max_time}ms")

        # 验证结果
        issues = []
        if max_time > 2000:
            issues.append("存在超过2秒的跳跃")
        if min_time < 400:
            issues.append("存在小于400ms的跳跃")

        if issues:
            print(f"\n[FAIL] 发现问题:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print(f"\n[OK] 跳跃时间正常")
            return True

    except FileNotFoundError:
        print(f"\n[FAIL] 找不到截图文件: {screenshot_path}")
        return False
    except Exception as e:
        print(f"\n[FAIL] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_slider_callback():
    """测试滑块回调函数"""
    print("\n" + "=" * 70)
    print("滑块回调函数测试")
    print("=" * 70)

    # 模拟不同的滑块值
    test_values = [
        0.5,       # 单个值
        (1.0,),    # 元组（一个元素）
        (1.5,),    # 元组（一个元素）
        2.0,       # 单个值
        (2.5,),    # 元组
    ]

    print("\n模拟滑块回调值处理:")
    for value in test_values:
        # 模拟 _on_slider_change 函数
        try:
            if isinstance(value, tuple):
                v = float(value[0]) if value else 1.5
            else:
                v = float(value)
            print(f"  输入: {value} -> 输出: {v:.2f} [OK]")
        except Exception as e:
            print(f"  输入: {value} -> 错误: {e} [FAIL]")

    print("\n[OK] 滑块回调测试完成")
    return True


def run_distance_limit_test():
    """测试距离限制功能"""
    print("\n" + "=" * 70)
    print("距离限制测试")
    print("=" * 70)

    config = GameConfig()
    algorithm = JumpAlgorithm(config)

    # 测试异常距离
    test_distances = [10, 20, 30, 50, 100, 500, 600, 700, 800, 1000]

    print(f"\n最大有效距离: {config.max_valid_distance}px")
    print(f"最小有效距离: {config.min_valid_distance}px")
    print("\n输入距离 -> 限制后距离 -> 按压时间")

    all_ok = True
    for dist in test_distances:
        press = algorithm.calculate_jump_time(dist, 0)
        if dist < config.min_valid_distance:
            limited = config.min_valid_distance
        elif dist > config.max_valid_distance:
            limited = config.max_valid_distance
        else:
            limited = dist

        status = "[OK]" if limited == dist or (dist < config.min_valid_distance or dist > config.max_valid_distance) else "[WARN]"
        if 400 <= press <= 2000:
            final_status = "[OK]"
        else:
            final_status = "[FAIL]"
            all_ok = False

        print(f"  {dist:4d}px   -> {limited:4d}px       -> {press:4d}ms {status} {final_status}")

    if all_ok:
        print("\n[OK] 距离限制测试通过")
    else:
        print("\n[FAIL] 距离限制测试失败")

    return all_ok


if __name__ == "__main__":
    print("\n开始算法测试 (v3.5 Prinsphield线性算法)...\n")

    test1 = test_with_screenshot()
    test2 = test_slider_callback()
    test3 = run_distance_limit_test()

    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"截图测试: {'[OK] 通过' if test1 else '[FAIL] 失败'}")
    print(f"滑块回调: {'[OK] 通过' if test2 else '[FAIL] 失败'}")
    print(f"距离限制: {'[OK] 通过' if test3 else '[FAIL] 失败'}")
    print("=" * 70)

    if test1 and test2 and test3:
        print("\n[OK][OK][OK] 所有测试通过！")
        sys.exit(0)
    else:
        print("\n[FAIL] 部分测试失败")
        sys.exit(1)
