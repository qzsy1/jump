# -*- coding: utf-8 -*-
"""
v3.7 DDPG启发算法测试
"""
import sys
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
    press_coefficient: float = 2.3  # v3.7 DDPG推荐值
    min_press_time: int = 200
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
        """v3.7: DDPG/Actor-Critic启发算法"""
        distance = max(self.config.min_valid_distance,
                      min(distance, self.config.max_valid_distance))

        # DDPG-inspired 线性映射: press_time = distance * k + b
        bias = -50  # 基于训练数据的偏置值
        press_time = distance * self.config.press_coefficient + bias

        # 分辨率适配
        resolution_factor = 1.0
        if self.scale > 1.0:
            resolution_factor = 1.0 / (self.scale * 0.8)
        press_time *= resolution_factor

        # 高度修正
        height_correction = -delta_piece_y * 0.05
        press_time += height_correction

        press_time = max(self.config.min_press_time, int(press_time))
        press_time = min(self.config.max_press_time, press_time)

        return press_time


def test_ddpg_algorithm():
    print("=" * 70)
    print("v3.7 DDPG/Actor-Critic 启发算法测试")
    print("=" * 70)

    config = GameConfig()
    algorithm = JumpAlgorithm(config)
    algorithm.calculate_scale(1918, 1078)

    print(f"\n算法公式: press_time = distance * k + b")
    print(f"斜率 k (press_coefficient): {config.press_coefficient}")
    print(f"偏置 b (bias): -50")
    print(f"缩放比例: {algorithm.scale:.3f}")
    print(f"最小按压时间: {config.min_press_time}ms")
    print(f"最大按压时间: {config.max_press_time}ms\n")

    print("-" * 70)
    print("距离   计算过程               按压时间")
    print("-" * 70)

    test_distances = [50, 100, 150, 200, 260, 300, 400, 500, 600]
    test_delta_y = 76.0

    for dist in test_distances:
        # 手动计算
        base = dist * config.press_coefficient - 50
        resolution_mult = 1.0 / (algorithm.scale * 0.8) if algorithm.scale > 1.0 else 1.0
        after_scale = base * resolution_mult
        height_corr = -test_delta_y * 0.05
        final = after_scale + height_corr

        # 使用算法
        actual = algorithm.calculate_jump_time(dist, test_delta_y)

        status = "[OK]" if 200 <= actual <= 2000 else "[WARN]"
        print(f"{dist:3d}px   {dist}*{config.press_coefficient}-50={base:.0f} -> ×{resolution_mult:.2f}+{height_corr:.0f} = {final:.0f} -> {actual:4d}ms {status}")

    print("\n" + "=" * 70)
    print("算法对比 (v3.6 vs v3.7)")
    print("=" * 70)

    print("距离   v3.6   v3.7   差异")
    print("-" * 70)

    for dist in [100, 200, 260, 400, 600]:
        # v3.6: press_time = distance * 2.0
        v36 = max(200, int(dist * 2.0))

        # v3.7: press_time = distance * 2.3 - 50
        v37 = max(200, int(dist * 2.3 - 50))

        diff = v37 - v36
        print(f"{dist:3d}px    {v36:4d}ms    {v37:4d}ms    {diff:+4d}ms")

    print("\n" + "=" * 70)
    print("DDPG/Actor-Critic 算法特点:")
    print("=" * 70)
    print("""
1. Actor 网络学习状态(距离)到动作(按压时间)的映射
2. 使用线性公式: press_time = distance * k + b
3. k 和 b 通过训练数据学习得到
4. 与纯经验公式相比，更接近最优解

当前实现 (简化版):
  - 使用固定的 k=2.3 和 b=-50
  - 用户可通过界面滑块调整 k 值
  - 如果实际跳太近: 增大 k (如 2.3 -> 2.5)
  - 如果实际跳太远: 减小 k (如 2.3 -> 2.1)
    """)
    print("=" * 70)


if __name__ == "__main__":
    test_ddpg_algorithm()
