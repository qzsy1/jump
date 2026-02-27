# -*- coding: utf-8 -*-
"""
诊断脚本 - 分析"长按"问题
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
    press_coefficient: float = 1.5  # 默认值
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

    def calculate_scale(self, img_width: int, img_height: int):
        base_width = 1920
        base_height = 1080
        self.scale = (img_width / base_width + img_height / base_height) / 2
        return self.scale

    def calculate_jump_time(self, distance: float, delta_piece_y: float = 0) -> int:
        """计算跳跃按压时间 - v3.5 Prinsphield线性算法"""
        distance = max(self.config.min_valid_distance,
                      min(distance, self.config.max_valid_distance))

        # 线性算法
        press_time = distance * self.config.press_coefficient

        # 分辨率适配
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


def diagnose_coefficient_issue():
    """诊断1: 按压系数问题"""
    print("=" * 70)
    print("诊断1: 按压系数对比")
    print("=" * 70)

    config = GameConfig()
    algorithm = JumpAlgorithm(config)
    algorithm.calculate_scale(1918, 1078)

    test_distance = 260.6
    test_delta_y = 76.0

    coefficients = [1.5, 2.045, 2.5, 3.0]

    print(f"\n测试距离: {test_distance}px, DeltaY: {test_delta_y}")
    print(f"缩放比例: {algorithm.scale:.3f}\n")
    print("按压系数 -> 计算过程 -> 最终按压时间")
    print("-" * 70)

    for coeff in coefficients:
        config.press_coefficient = coeff
        press_time = algorithm.calculate_jump_time(test_distance, test_delta_y)

        # 手动计算过程
        base_time = test_distance * coeff
        print(f"{coeff:.3f}     -> {base_time:.0f}ms × {1.0:.1f} + {-test_delta_y * 0.5:.0f}ms -> {press_time}ms")

    print("\n结论: Prinsphield 原始系数 2.045 vs 当前默认 1.5，差值 36%")
    return True


def diagnose_height_correction():
    """诊断2: 高度修正问题"""
    print("\n" + "=" * 70)
    print("诊断2: 高度修正影响")
    print("=" * 70)

    config = GameConfig()
    config.press_coefficient = 1.5
    algorithm = JumpAlgorithm(config)
    algorithm.calculate_scale(1918, 1078)

    test_distance = 260.6

    # 不同的 delta_y 值
    delta_tests = [
        (-100, "棋子在屏幕中心上方（高处）"),
        (0, "棋子在屏幕中心"),
        (76, "棋子在屏幕中心下方（低处）"),
        (150, "棋子在更下方"),
    ]

    print(f"\n测试距离: {test_distance}px, 按压系数: 1.5\n")
    print("DeltaY   说明                    按压时间")
    print("-" * 70)

    for delta_y, desc in delta_tests:
        press_time = algorithm.calculate_jump_time(test_distance, delta_y)
        correction = -delta_y * 0.5
        print(f"{delta_y:4.0f}   {desc:20s} -> {press_time}ms (修正: {correction:+.0f}ms)")

    print("\n问题分析:")
    print("  - 棋子越低(DeltaY为正)，按压时间越短（减去修正值）")
    print("  - 但游戏逻辑: 棋子越低，应该按更长才对！")
    print("  - 这个修正系数 0.5 可能太大了")

    return True


def diagnose_platform_detection():
    """诊断3: 平台检测问题分析"""
    print("\n" + "=" * 70)
    print("诊断3: 平台检测可能的问题")
    print("=" * 70)

    print("""
当前平台检测逻辑:
  1. 搜索棋子左右两侧的所有亮色平台
  2. 按平台大小（像素数量）排序
  3. 选择最大的平台作为目标

潜在问题:
  ┌────────────────────────────────────────────────────────────┐
  │                                                            │
  │   [大平台 - 当前位置]              [小平台 - 目标]         │
  │                                                            │
  │        ● 棋子                          → 目标             │
  │                                                            │
  │   如果当前平台 > 目标平台，算法可能选中当前平台！          │
  │   → 计算距离接近 0                                         │
  │   → 但 min_press_time=400ms 限制                          │
  │   → 结果: 按 400ms 跳到错误位置                           │
  │                                                            │
  └────────────────────────────────────────────────────────────┘

建议修复方案:
  方案1: 排除棋子附近的平台（增加排除半径）
  方案2: 优先选择距离较远的平台
  方案3: 记录上次位置，选择方向相反的平台
    """)

    return True


def diagnose_min_press_time():
    """诊断4: 最小按压时间问题"""
    print("\n" + "=" * 70)
    print("诊断4: 最小按压时间限制")
    print("=" * 70)

    config = GameConfig()
    config.press_coefficient = 1.5
    algorithm = JumpAlgorithm(config)
    algorithm.calculate_scale(1918, 1078)

    print(f"\n最小按压时间: {config.min_press_time}ms")
    print(f"按压系数: 1.5\n")

    print("距离     原始时间    实际时间    说明")
    print("-" * 70)

    for dist in [30, 50, 100, 150, 200, 260]:
        raw_time = dist * 1.5
        actual_time = algorithm.calculate_jump_time(dist, 0)
        if raw_time < 400:
            status = "被限制到400ms"
        else:
            status = "正常"
        print(f"{dist:3d}px    {raw_time:3.0f}ms       {actual_time:4d}ms     {status}")

    print("\n问题:")
    print("  - 短距离（<267px）都会被限制到 400ms")
    print("  - 如果实际只需要 200ms，按 400ms 就会跳太远")
    print("  - 建议: 降低 min_press_time 到 200ms")

    return True


if __name__ == "__main__":
    print("\n开始诊断分析...\n")

    diagnose_coefficient_issue()
    diagnose_height_correction()
    diagnose_platform_detection()
    diagnose_min_press_time()

    print("\n" + "=" * 70)
    print("诊断总结")
    print("=" * 70)
    print("""
可能导致"长按"问题的原因（按优先级排序）:

1. 【最可能】平台检测错误 - 选中了当前平台而不是目标平台
   → 计算距离接近 0，但被 min_press_time=400ms 限制
   → 对于短距离来说 400ms 太长

2. 【很可能】按压系数太小 - 默认 1.5 vs 参考值 2.045
   → 如果需要更长的按压时间，这个值太保守了

3. 【可能】高度修正反向 - 棋子越低按压越短
   → 与游戏逻辑相反

4. 【次要】最小按压时间限制 - 400ms 对短距离跳跃太长

建议修复步骤:
1. 首先修复平台检测 - 排除棋子附近的当前平台
2. 调整默认按压系数到 2.0
3. 降低 min_press_time 到 200ms
    """)
    print("=" * 70)
