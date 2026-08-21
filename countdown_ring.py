"""
countdown_ring.py —— Kivy 倒计时圆环组件
"""

from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock
from kivy.properties import NumericProperty, ColorProperty
from config import COLORS


class CountdownRing(Widget):
    """
    圆形倒计时指示器。
    - progress: 0~1，1 表示满，0 表示耗尽
    - 颜色随剩余时间变化：蓝 → 橙 → 红
    """

    progress = NumericProperty(1.0)
    ring_color = ColorProperty(COLORS["timer_ring"])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw, progress=self._on_progress)
        self._draw()

    def _on_progress(self, *args):
        p = self.progress
        if p > 0.5:
            self.ring_color = COLORS["timer_ring"]
        elif p > 0.2:
            self.ring_color = COLORS["timer_warning"]
        else:
            self.ring_color = COLORS["timer_danger"]
        self._draw()

    def _draw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # 背景圆环
            Color(*COLORS["bg"])
            d = min(self.width, self.height) * 0.9
            cx = self.center_x - d / 2
            cy = self.center_y - d / 2
            Ellipse(pos=(cx, cy), size=(d, d), color=Color(*COLORS["text"], 0.08))

            # 进度弧
            Color(*self.ring_color)
            # Kivy Line 的 ellipse 参数：(x, y, w, h, angle_start, angle_end)
            sweep = 360.0 * max(0.0, min(1.0, self.progress))
            Line(
                ellipse=(cx, cy, d, d, 0, sweep),
                width=8,
                cap="round",
            )
