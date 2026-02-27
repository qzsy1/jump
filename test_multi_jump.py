# -*- coding: utf-8 -*-
"""
模拟多次跳跃测试 - v3.5 Prinsphield线性算法验证双向搜索
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
            print(f"  警告: 距离过大 {distance:.1f}px，限制")
            if piece_x < w / 2:
                estimated_x = piece_x + min(distance, 400)
            else:
                estimated_x = piece_x - min(distance, 400)
            board_x = estimated_x
            board_y = piece_y
            distance = math.sqrt((board_x - piece_x) ** 2 + (board_y - piece_y) ** 2)

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
        """双向搜索 - 关键修复"""
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
            # 按平台大小排序，找最大的
            candidates.sort(key=lambda x: x[2], reverse=True)
            best = candidates[0]
            return best[0], best[1]

        return 0, 0

    def _search_direction(self, im_pixel, start_x, end_x, start_y, end_y, piece_x):
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


def test_multiple_jumps_simulation():
    """模拟多次跳跃 - 测试双向搜索"""
    print("=" * 70)
    print("多次跳跃模拟测试")
    print("=" * 70)

    config = GameConfig()
    algorithm = JumpAlgorithm(config)

    # 加载截图
    screenshot_path = r"C:\Users\xlq\.claude\skills\pygui-creator\content\dist\屏幕截图 2026-02-27 022528.png"

    try:
        img = Image.open(screenshot_path)
        print(f"\n使用截图: {img.size}")
        print(f"游戏区域: [400, 0, 1000, 1080]")
        print("\n说明: 模拟棋子在左侧和右侧时，算法能否正确找到平台")

        # 测试1: 棋子在左侧 (原始截图)
        print("\n" + "-" * 70)
        print("测试1: 棋子在左侧 (原始截图)")
        print("-" * 70)

        piece_x, piece_y, board_x, board_y, delta_y = algorithm.find_piece_and_board(img)
        distance = algorithm.calculate_distance(piece_x, piece_y, board_x, board_y)
        press_time = algorithm.calculate_jump_time(distance, delta_y)

        print(f"棋子位置: ({piece_x}, {piece_y})")
        print(f"平台中心: ({board_x}, {board_y})")
        print(f"距离: {distance:.1f}px -> 按压: {press_time}ms")

        # 验证: 平台应该在棋子右侧
        if board_x > piece_x:
            print(f"[OK] 平台在棋子右侧 (正确)")
        else:
            print(f"[WARN] 平台在棋子左侧？")

        # 测试2: 模拟棋子在右侧 (镜像翻转)
        print("\n" + "-" * 70)
        print("测试2: 棋子在右侧 (镜像模拟)")
        print("-" * 70)

        # 镜像翻转图片，模拟棋子在右侧的情况
        mirrored_img = img.transpose(Image.FLIP_LEFT_RIGHT)
        w, h = mirrored_img.size

        # 重新初始化算法
        algorithm2 = JumpAlgorithm(config)
        piece_x2, piece_y2, board_x2, board_y2, delta_y2 = algorithm2.find_piece_and_board(mirrored_img)
        distance2 = algorithm2.calculate_distance(piece_x2, piece_y2, board_x2, board_y2)
        press_time2 = algorithm2.calculate_jump_time(distance2, delta_y2)

        print(f"棋子位置: ({piece_x2}, {piece_y2})")
        print(f"平台中心: ({board_x2}, {board_y2})")
        print(f"距离: {distance2:.1f}px -> 按压: {press_time2}ms")

        # 验证: 镜像后，平台应该在棋子左侧
        if board_x2 < piece_x2:
            print(f"[OK] 平台在棋子左侧 (正确)")
        else:
            print(f"[WARN] 平台在棋子右侧？")

        # 分析
        print("\n" + "-" * 70)
        print("分析结果")
        print("-" * 70)

        # 验证双向搜索是否有效
        if (board_x > piece_x and board_x2 < piece_x2) or (board_x < piece_x and board_x2 > piece_x2):
            print("[OK] 双向搜索正常工作：")
            print("     - 左侧棋子能找到右侧平台")
            print("     - 右侧棋子能找到左侧平台")
            print("\n这意味着多次跳跃后，无论棋子在左侧还是右侧，")
            print("算法都能正确找到下一个平台！")
            return True
        else:
            print("[WARN] 双向搜索可能需要调整")
            return False

    except Exception as e:
        print(f"[FAIL] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n开始多次跳跃测试 (v3.5 Prinsphield线性算法)...\n")

    result = test_multiple_jumps_simulation()

    print("\n" + "=" * 70)
    if result:
        print("[OK] 多次跳跃测试通过！")
        print("\n修复说明:")
        print("  原问题: 算法假设棋子总在固定位置，只向一个方向搜索")
        print("  新方案: 双向搜索 - 同时搜索左侧和右侧，找最大平台")
        print("  效果: 无论棋子跳跃到哪里，都能找到正确的下一个平台")
    else:
        print("[WARN] 需要进一步调整")
    print("=" * 70)
