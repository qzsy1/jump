# -*- coding: utf-8 -*-
"""
v3.6 参数测试
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
    press_coefficient: float = 2.0  # v3.6 新值
    min_press_time: int = 200  # v3.6 新值
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

    def calculate_scale(self, img_width: int, img_height: int):
        self.scale = (img_width / 1920 + img_height / 1080) / 2
        return self.scale

    def calculate_jump_time(self, distance: float, delta_piece_y: float = 0) -> int:
        """v3.6: 加大排除半径，调整参数"""
        distance = max(self.config.min_valid_distance,
                      min(distance, self.config.max_valid_distance))

        press_time = distance * self.config.press_coefficient

        resolution_factor = 1.0
        if self.scale > 1.0:
            resolution_factor = 1.0 / self.scale
        press_time *= resolution_factor

        # v3.6: 减小高度修正系数 0.5 -> 0.1
        height_correction = -delta_piece_y * 0.1
        press_time += height_correction

        press_time = max(self.config.min_press_time, int(press_time))
        press_time = min(self.config.max_press_time, press_time)

        return press_time


def test_v36():
    print("=" * 70)
    print("v3.6 参数测试 - 对比 v3.5")
    print("=" * 70)

    config = GameConfig()
    algorithm = JumpAlgorithm(config)
    algorithm.calculate_scale(1918, 1078)

    test_distance = 260.6
    test_delta_y = 76.0

    print(f"\n测试距离: {test_distance}px, DeltaY: {test_delta_y}")
    print(f"缩放比例: {algorithm.scale:.3f}\n")

    # v3.5 参数
    old_coeff = 1.5
    old_min = 400
    old_correction = 0.5

    # v3.6 参数
    new_coeff = 2.0
    new_min = 200
    new_correction = 0.1

    print("版本  系数  最小按压  修正系数  按压时间")
    print("-" * 70)

    # v3.5 计算
    base = test_distance * old_coeff
    corr = -test_delta_y * old_correction
    v35_time = max(old_min, int(base + corr))
    print(f"v3.5  {old_coeff:.1f}   {old_min}ms      {old_correction:.1f}     {v35_time}ms")

    # v3.6 计算
    base = test_distance * new_coeff
    corr = -test_delta_y * new_correction
    v36_time = max(new_min, int(base + corr))
    print(f"v3.6  {new_coeff:.1f}   {new_min}ms      {new_correction:.1f}     {v36_time}ms")

    print(f"\n差异: v3.6 比 v3.5 {'多' if v36_time > v35_time else '少'} {abs(v36_time - v35_time)}ms")

    # 测试不同距离
    print("\n" + "-" * 70)
    print("距离   v3.5按压  v3.6按压  差异")
    print("-" * 70)

    for dist in [50, 100, 150, 200, 260, 300, 400, 500, 600]:
        # v3.5
        base = dist * old_coeff
        v35 = max(old_min, int(base + corr))

        # v3.6
        base = dist * new_coeff
        v36 = max(new_min, int(base + corr))

        diff = v36 - v35
        print(f"{dist:3d}px    {v35:3d}ms      {v36:3d}ms    {diff:+3d}ms")

    print("\n" + "=" * 70)
    print("关键变化:")
    print("1. 加大平台排除半径: 80px → 150px (避免选中当前平台)")
    print("2. 按压系数: 1.5 → 2.0")
    print("3. 最小按压: 400ms → 200ms (短距离更准确)")
    print("4. 高度修正: 0.5 → 0.1 (减少过度修正)")
    print("=" * 70)


if __name__ == "__main__":
    test_v36()
