"""
celebrate.py —— 答对时的撒花庆祝动画
"""

import random
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty, BooleanProperty
from config import COLORS


CONFETTI_COLORS = [
    COLORS["primary"], COLORS["secondary"], COLORS["accent"],
    COLORS["purple"], COLORS["pink"], COLORS["orange"], COLORS["correct"],
]


class ConfettiPiece:
    """单片纸屑"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(3, 8)
        self.size = random.randint(8, 18)
        self.color = random.choice(CONFETTI_COLORS)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-8, 8)
        self.shape = random.choice(["circle", "rect"])
        self.alive = True


class CelebrateOverlay(Widget):
    """
    覆盖在界面上的撒花层。
    调用 burst() 触发一次撒花。
    """

    opacity = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.particles = []
        self._event = None

    def burst(self, cx=None, cy=None):
        """在指定位置（默认屏幕中下方）爆发一次"""
        if cx is None:
            cx = self.center_x
        if cy is None:
            cy = self.center_y * 0.6

        self.particles.clear()
        for _ in range(80):
            p = ConfettiPiece(cx + random.uniform(-30, 30),
                              cy + random.uniform(-20, 20))
            self.particles.append(p)

        self.opacity = 1.0
        if self._event:
            self._event.cancel()
        self._event = Clock.schedule_interval(self._update, 1 / 60)
        # 2 秒后自动淡出
        Clock.schedule_once(self._fade_out, 1.5)

    def _fade_out(self, *args):
        anim = Animation(opacity=0, duration=0.5)
        anim.bind(on_complete=lambda *a: self._stop())
        anim.start(self)

    def _stop(self, *args):
        if self._event:
            self._event.cancel()
            self._event = None
        self.particles.clear()
        self.canvas.clear()

    def _update(self, dt):
        self.canvas.clear()
        h = self.height
        with self.canvas:
            for p in self.particles:
                p.x += p.vx
                p.y += p.vy
                p.vy -= 0.25  # 重力
                p.rotation += p.rot_speed
                if p.y < -20:
                    p.alive = False
                Color(*p.color, self.opacity)
                if p.shape == "circle":
                    Ellipse(pos=(p.x, p.y), size=(p.size, p.size))
                else:
                    Rectangle(pos=(p.x, p.y), size=(p.size, p.size * 0.6))
            # 移除死亡粒子
            self.particles = [p for p in self.particles if p.alive]
        if not self.particles:
            self._stop()
