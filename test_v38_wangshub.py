# -*- coding: utf-8 -*-
"""
v3.8 wangshub 经典线性算法测试
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
    press_coefficient: float = 1.5  # wangshub 经典值
    min_press_time: int = 200  # wangshub 最小按压时间
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

    def calculate_jump_time(self, distance: float, delta_piece_y: float = 0) -> int:
        """v3.8: wangshub 经典线性算法"""
        distance = max(self.config.min_valid_distance,
                      min(distance, self.config.max_valid_distance))

        # wangshub 算法: press_time = distance * press_coefficient
        press_time = distance * self.config.press_coefficient

        # wangshub 算法: 设置 200ms 是最小的按压时间
        press_time = max(press_time, 200)

        press_time = int(press_time)

        return press_time


def test_wangshub_algorithm():
    print("=" * 70)
    print("v3.8 wangshub 经典线性算法测试")
    print("=" * 70)

    config = GameConfig()
    algorithm = JumpAlgorithm(config)

    print("\n核心公式: press_time = distance * press_coefficient")
    print("press_coefficient = %s" % config.press_coefficient)
    print("min_press_time = %dms" % config.min_press_time)
    print("max_valid_distance = %dpx\n" % config.max_valid_distance)

    print("-" * 70)
    print("距离   计算过程            按压时间")
    print("-" * 70)

    test_distances = [30, 50, 100, 150, 200, 260, 300, 400, 500, 600]

    for dist in test_distances:
        raw_time = dist * config.press_coefficient
        final_time = max(raw_time, config.min_press_time)

        status = "[OK]" if config.min_press_time <= final_time <= config.max_press_time else "[WARN]"
        print("%dpx   %d*%s=%.0f -> max(%.0f,200) = %dms %s" % (dist, dist, config.press_coefficient, raw_time, raw_time, final_time, status))

    print("\n" + "=" * 70)
    print("算法对比 (v3.7 vs v3.8)")
    print("=" * 70)

    print("距离   v3.7 DDPG   v3.8 wangshub   差异")
    print("-" * 70)

    for dist in [100, 200, 260, 400, 600]:
        # v3.7: press_time = distance * 2.3 - 50
        v37_base = dist * 2.3 - 50
        v37 = max(v37_base, 200)

        # v3.8: press_time = distance * 1.5
        v38_base = dist * 1.5
        v38 = max(v38_base, 200)

        diff = v38 - v37
        print("%dpx    %dms         %dms            %+dms" % (dist, v37, v38, diff))

    print("\n" + "=" * 70)
    print("wangshub 算法特点:")
    print("=" * 70)
    print("""
1. 极简线性公式: press_time = distance * coefficient
2. 无偏置项: 不需要调整 bias 参数
3. 无分辨率适配: coefficient 可手动调整适应不同设备
4. 无高度修正: 保持简洁稳定
5. 最小按压 200ms: 短距离更精确

参数调整:
  - 跳得太近: 增大 coefficient (如 1.5 -> 1.8)
  - 跳得太远: 减小 coefficient (如 1.5 -> 1.2)
  - 完美: 保持 1.5

这是最经典、最稳定的算法版本！
    """)
    print("=" * 70)


if __name__ == "__main__":
    test_wangshub_algorithm()
