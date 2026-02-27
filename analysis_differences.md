# wangshub 原程序 vs 当前实现 对比分析

## 关键差异总结

### 差异1: 【最重要】对称中心修正 - wangshub 有，我们没有！

**wangshub 原程序** (第183-193行):
```python
# 首先找到游戏的对称中心，由对称中心做辅助线与x=board_x直线的交点即为棋盘的中心位置
# 有了对称中心，可以知道棋子在棋盘上面的相对位置（偏高或偏低），偏高的话测量值比实际值大，
# 偏低相反。最后通过delta_piece_y来对跳跃时间进行微调

center_x = w / 2 + (24 / 1080) * w
center_y = h / 2 + (17 / 1920) * h

if piece_x > center_x:
    board_y = round((25.5 / 43.5) * (board_x - center_x) + center_y)
    delta_piece_y = piece_y - round((25.5 / 43.5) * (piece_x - center_x) + center_y)
else:
    board_y = round(-(25.5 / 43.5) * (board_x - center_x) + center_y)
    delta_piece_y = piece_y - round(-(25.5 / 43.5) * (piece_x - center_x) + center_y)
```

**我们的实现**:
```python
# find_piece_and_board 返回的 delta_piece_y 始终是 0！
# 因为我们的实现没有计算对称中心，也没有计算真实的 delta_piece_y

delta_piece_y = 0  # 永远是 0，所以高度修正不起作用！
```

**影响**: 这是精度不高的主要原因！
- wangshub 根据棋子在屏幕上的实际位置动态调整 board_y
- 我们的实现 board_y 只是简单检测到的平台Y坐标
- delta_piece_y 应该是棋子实际Y vs "标准位置Y" 的差值

---

### 差异2: 平台检测抗干扰机制 - wangshub 有，我们没有

**wangshub 原程序** (第169-178行):
```python
# 检查Y轴下面5个像素，和背景色相同，那么是干扰
# 这样可以排除一些误检测的亮色区域，提高准确性

ver_pixel = im_pixel[j, i + 5]
if abs(pixel[0] - last_pixel[0]) + abs(pixel[1] - last_pixel[1]) + abs(pixel[2] - last_pixel[2]) > 10 \
        and abs(ver_pixel[0] - last_pixel[0]) + abs(ver_pixel[1] - last_pixel[1]) + abs(ver_pixel[2] - last_pixel[2]) > 10:
    board_x_sum += j
    board_x_c += 1
```

**我们的实现**:
```python
# 没有这种抗干扰机制
# 简单地检测亮色区域，容易被误判
```

**影响**: 可能选中错误的平台或噪声

---

### 差异3: 扫描起始点检测 - wangshub 有，我们没有

**wangshub 原程序** (第116-126行):
```python
# 以 50px 步长，尝试探测 scan_start_y
# 检测到不是纯色的线，则记录 scan_start_y 的值

for i in range(int(h / 3), int(h * 2 / 3), 50):
    last_pixel = im_pixel[0, i]
    for j in range(1, w):
        pixel = im_pixel[j, i]
        if pixel != last_pixel:
            scan_start_y = i - 50
            break
```

**我们的实现**:
```python
# 直接从固定的 Y 范围开始扫描，没有智能起始点检测
search_y_start = max(int(h * 0.2), int(piece_y - 150))
```

**影响**: 可能错过一些边界情况

---

### 差异4: 棋子颜色检测条件差异

**wangshub 原程序** (第135-137行):
```python
if (50 < pixel[0] < 60) and (53 < pixel[1] < 63) and (95 < pixel[2] < 110):
```

**我们的实现** (第133-134行):
```python
purple = (r < g and g < b and r > 25 and r < 100 and
         g > 5 and g < 80 and b > 50 and b < 140)
```

**影响**: 检测条件不同，可能影响棋子识别准确性

---

### 差异5: 平台亮色检测条件

**wangshub 原程序**:
- 检测平台（亮色）
- 检查Y轴下面像素和背景色差异

**我们的实现** (第237-242行):
```python
# 检测平台（亮色）
brightness = r + g + b
if brightness > 500 and r > 150 and g > 150 and b > 150:
    # 排除纯白色背景
    if brightness < 750:
        bright_pixels.append(j)
```

**影响**: 我们的亮色条件更宽泛，但可能引入噪声

---

### 差异6: 备用方案 - 我们简化了太多

**wangshub 原程序**的备用检测更复杂：
- 从上顶点往下搜索
- 检测花纹点 (r245 g245 b245) 用于弥补错误

**我们的实现** (第204-218行):
```python
# 非常简单的备用方案
bright_pixels = []
for i in range(search_y_start, search_y_end):
    for j in range(50, w - 50):
        if abs(j - piece_x) < int(80 * self.scale):
            continue
        # 简单检测亮色
        ...
if bright_pixels:
    avg_x = int(sum([p[0] for p in bright_pixels]) / len(bright_pixels))
    avg_y = int(sum([p[1] for p in bright_pixels]) / len(bright_pixels))
```

**影响**: 备用方案不够准确

---

## 核心问题总结

### 1. 【最严重】delta_piece_y 永远是 0
**原因**: 没有实现对称中心计算
**影响**: 高度修正完全不起作用，按压时间无法根据棋子位置微调

### 2. 平台检测可能选中错误目标
**原因**:
- 没有抗干扰机制
- 备用方案太简化
- 双向搜索可能选中错误的平台

### 3. 棋子检测条件略有差异
**原因**: 颜色范围不同

---

## 修复建议

### 优先级 1: 实现对称中心计算
```python
def _find_symmetry_center(self, w, h):
    """计算游戏对称中心"""
    center_x = w / 2 + (24 / 1080) * w
    center_y = h / 2 + (17 / 1920) * h
    return center_x, center_y

def _calculate_delta_piece_y(self, piece_x, piece_y, center_x, center_y):
    """计算棋子Y轴偏移（相对于对称中心）"""
    if piece_x > center_x:
        expected_piece_y = round((25.5 / 43.5) * (piece_x - center_x) + center_y)
    else:
        expected_piece_y = round(-(25.5 / 43.5) * (piece_x - center_x) + center_y)

    delta_piece_y = piece_y - expected_piece_y
    return delta_piece_y
```

### 优先级 2: 增加平台检测抗干扰
```python
# 检查Y轴下面5个像素，和背景色相同，那么是干扰
ver_pixel = im_pixel[j, i + 5]
if abs(pixel[0] - last_pixel[0]) + abs(pixel[1] - last_pixel[1]) + abs(pixel[2] - last_pixel[2]) > 10:
    # 跳过这个像素，可能是干扰
    continue
```

### 优先级 3: 改进备用检测方案

---

## 测试验证

要验证问题，可以：
1. 打印 delta_piece_y 值 - 如果始终是 0 就说明问题
2. 观察平台检测是否选中正确的平台
3. 观察棋子检测是否准确
