"""
main.py —— Kivy 主应用：界面、游戏流程、事件处理
"""

import os
import time
import random
import threading

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.animation import Animation
from kivy.metrics import dp

from config import (
    APP_DIR, AVATAR_DIR, COLORS, DIFFICULTY_CONFIG,
    get_time_for_question, MAX_LEADERBOARD,
)
from question_generator import QuestionGenerator, Question
from leaderboard import Leaderboard
from voice import VoiceRecognizer
from tts import TTS
from countdown_ring import CountdownRing
from celebrate import CelebrateOverlay
import os
from kivy.core.text import LabelBase
from kivy.lang import Builder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CN_FONT = os.path.join(
    BASE_DIR,
    "fonts",
    "NotoSansSC-Regular.ttf"
)

LabelBase.register(
    name="CNFont",
    fn_regular=CN_FONT
)

Builder.load_string(f"""
<Label>:
    font_name: "{CN_FONT}"

<Button>:
    font_name: "{CN_FONT}"

<TextInput>:
    font_name: "{CN_FONT}"
""")
# ============================================================
# 全局 Window 设置
# ============================================================
Window.clearcolor = get_color_from_hex(COLORS["bg"])
# 横屏优先（平板）
Window.allow_screenshot = True


# ============================================================
# 工具函数
# ============================================================
def rounded_rect(canvas, x, y, w, h, r, color):
    with canvas:
        Color(*color)
        RoundedRectangle(pos=(x, y), size=(w, h), radius=[r])


# ============================================================
# 难度选择界面
# ============================================================
class DifficultyScreen(BoxLayout):
    """难度选择 + 开始提示"""

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref
        self.orientation = "vertical"
        self.spacing = dp(20)
        self.padding = dp(40)

        # 标题
        self.title = Label(
            text="🌈 数学小天才 🌈",
            font_size=dp(48),
            color=get_color_from_hex(COLORS["text"]),
            bold=True,
            size_hint=(1, 0.2),
        )
        self.add_widget(self.title)

        # 副标题
        self.subtitle = Label(
            text='说"开始"或点击按钮开始游戏',
            font_size=dp(22),
            color=get_color_from_hex(COLORS["text"]),
            size_hint=(1, 0.1),
        )
        self.add_widget(self.subtitle)

        # 难度按钮
        btn_layout = BoxLayout(
            orientation="horizontal",
            spacing=dp(20),
            size_hint=(1, 0.4),
        )

        for level in ("easy", "normal", "hard"):
            cfg = DIFFICULTY_CONFIG[level]
            btn = Button(
                text=f"{cfg['label']}\n{cfg['age_range']}",
                font_size=dp(24),
                background_color=get_color_from_hex(self._btn_color(level)),
                color=get_color_from_hex(COLORS["text_light"]),
                size_hint=(0.33, 1),
                halign="center",
            )
            btn.bind(on_release=lambda inst, lv=level: self._on_select(lv))
            btn_layout.add_widget(btn)

        self.add_widget(btn_layout)

        # 排行榜按钮
        lb_btn = Button(
            text="🏆 查看排行榜",
            font_size=dp(22),
            background_color=get_color_from_hex(COLORS["accent"]),
            color=get_color_from_hex(COLORS["text"]),
            size_hint=(0.5, 0.12),
            pos_hint={"center_x": 0.5},
        )
        lb_btn.bind(on_release=self._show_leaderboard)
        self.add_widget(lb_btn)

        # 状态提示
        self.status = Label(
            text="",
            font_size=dp(18),
            color=get_color_from_hex(COLORS["text"]),
            size_hint=(1, 0.1),
        )
        self.add_widget(self.status)

        self.selected_difficulty = None

    def _btn_color(self, level):
        return {
            "easy": COLORS["correct"],
            "normal": COLORS["button"],
            "hard": COLORS["primary"],
        }[level]

    def _on_select(self, level):
        self.selected_difficulty = level
        self.status.text = f"已选择：{DIFFICULTY_CONFIG[level]['label']} 准备开始…"
        self.app.start_game(level)

    def _show_leaderboard(self, *args):
        self.app.show_leaderboard()


# ============================================================
# 游戏主界面
# ============================================================
class GameScreen(FloatLayout):
    """游戏进行时界面"""

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref

        # ---- 顶部信息栏 ----
        self.top_bar = BoxLayout(
            orientation="horizontal",
            size_hint=(1, 0.1),
            pos_hint={"top": 1},
            padding=dp(15),
            spacing=dp(15),
        )
        self.score_label = Label(
            text="得分: 0", font_size=dp(22),
            color=get_color_from_hex(COLORS["text"]),
            size_hint=(0.25, 1), halign="left",
        )
        self.progress_label = Label(
            text="题目: 0/0", font_size=dp(22),
            color=get_color_from_hex(COLORS["text"]),
            size_hint=(0.25, 1),
        )
        self.wrong_label = Label(
            text="❌: 0", font_size=dp(22),
            color=get_color_from_hex(COLORS["wrong"]),
            size_hint=(0.25, 1),
        )
        self.back_btn = Button(
            text="← 退出",
            font_size=dp(18),
            background_color=get_color_from_hex(COLORS["text"]),
            color=get_color_from_hex(COLORS["text_light"]),
            size_hint=(0.15, 0.8),
        )
        self.back_btn.bind(on_release=lambda *a: self.app.exit_to_menu())
        for w in [self.score_label, self.progress_label, self.wrong_label, self.back_btn]:
            self.top_bar.add_widget(w)
        self.add_widget(self.top_bar)

        # ---- 倒计时圆环 ----
        self.countdown = CountdownRing(
            size_hint=(0.35, 0.35),
            pos_hint={"center_x": 0.5, "center_y": 0.72},
        )
        self.add_widget(self.countdown)

        # ---- 题目显示 ----
        self.question_label = Label(
            text="",
            font_size=dp(64),
            color=get_color_from_hex(COLORS["text"]),
            bold=True,
            size_hint=(1, 0.2),
            pos_hint={"center_x": 0.5, "center_y": 0.50},
        )
        self.add_widget(self.question_label)

        # ---- 反馈提示（"你真棒"/"再想想"） ----
        self.feedback_label = Label(
            text="",
            font_size=dp(36),
            color=get_color_from_hex(COLORS["correct"]),
            bold=True,
            size_hint=(1, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.38},
        )
        self.add_widget(self.feedback_label)

        # ---- 数字键盘 ----
        self.keypad = self._build_keypad()
        self.add_widget(self.keypad)

        # ---- 撒花层 ----
        self.celebrate = CelebrateOverlay(
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.add_widget(self.celebrate)

        # 游戏状态
        self.current_question = None
        self.score = 0
        self.wrong_count = 0
        self.q_index = 0
        self.total_questions = 0
        self.difficulty = "easy"
        self.current_time_limit = 20
        self._timer_event = None
        self._time_left = 0
        self._answer_locked = False  # 防止重复提交

    def _build_keypad(self):
        """数字键盘 + 提交/清除"""
        layout = GridLayout(
            cols=3,
            spacing=dp(10),
            size_hint=(0.6, 0.32),
            pos_hint={"center_x": 0.5, "y": 0.03},
            padding=dp(10),
        )
        self.input_display = TextInput(
            text="",
            font_size=dp(36),
            readonly=True,
            halign="center",
            size_hint=(1, 0.2),
            multiline=False,
            background_color=get_color_from_hex("#FFFFFF"),
            foreground_color=get_color_from_hex(COLORS["text"]),
        )
        # 用一个 BoxLayout 包装 input + 按钮
        wrapper = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint=(0.6, 0.36),
            pos_hint={"center_x": 0.5, "y": 0.03},
        )
        wrapper.add_widget(self.input_display)

        btn_layout = GridLayout(cols=3, spacing=dp(8))

        # 数字按钮 1-9
        self.num_buttons = {}
        for i in range(1, 10):
            btn = Button(
                text=str(i),
                font_size=dp(28),
                background_color=get_color_from_hex(COLORS["button"]),
                color=get_color_from_hex(COLORS["text_light"]),
            )
            btn.bind(on_release=lambda inst, n=i: self._press_number(n))
            self.num_buttons[i] = btn
            btn_layout.add_widget(btn)

        # 0
        btn0 = Button(
            text="0",
            font_size=dp(28),
            background_color=get_color_from_hex(COLORS["button"]),
            color=get_color_from_hex(COLORS["text_light"]),
        )
        btn0.bind(on_release=lambda inst: self._press_number(0))
        btn_layout.add_widget(btn0)

        # 清除
        clear_btn = Button(
            text="清除",
            font_size=dp(22),
            background_color=get_color_from_hex(COLORS["wrong"]),
            color=get_color_from_hex(COLORS["text_light"]),
        )
        clear_btn.bind(on_release=lambda inst: self._clear_input())
        btn_layout.add_widget(clear_btn)

        # 提交
        submit_btn = Button(
            text="提交 ✓",
            font_size=dp(22),
            background_color=get_color_from_hex(COLORS["correct"]),
            color=get_color_from_hex(COLORS["text_light"]),
        )
        submit_btn.bind(on_release=lambda inst: self._submit_answer())
        btn_layout.add_widget(submit_btn)

        wrapper.add_widget(btn_layout)
        # 我们用一个 FloatLayout 作为根
        root = FloatLayout(size_hint=(1, 0.42), pos_hint={"x": 0, "y": 0})
        root.add_widget(wrapper)
        return root

    # ---- 输入处理 ----
    def _press_number(self, n):
        if self._answer_locked:
            return
        cur = self.input_display.text
        if len(cur) < 5:
            self.input_display.text = cur + str(n)

    def _clear_input(self):
        self.input_display.text = ""

    # ---- 游戏流程 ----
    def start_game(self, difficulty):
        """由 App 调用，开始一轮游戏"""
        self.difficulty = difficulty
        cfg = DIFFICULTY_CONFIG[difficulty]
        self.score = 0
        self.wrong_count = 0
        self.q_index = 0
        self.total_questions = cfg["total_questions"]
        self._update_top_bar()

        # 提示语音
        self.app.tts.speak("准备好了请说开始")
        self.feedback_label.text = '🎤 说"开始"或点击这里开始'
        self.feedback_label.color = get_color_from_hex(COLORS["text"])
        # 点击任意位置也可开始（给没麦克风的设备）
        self.bind(on_touch_down=self._on_touch_start)

    def _on_touch_start(self, *args):
        # 第一次触摸即开始（仅用于无语音场景）
        self.unbind(on_touch_down=self._on_touch_start)
        self._begin_first_question()

    def _begin_first_question(self):
        self.feedback_label.text = ""
        self._next_question()

    def _next_question(self):
        """出下一题"""
        if self.q_index >= self.total_questions:
            self._end_game()
            return

        cfg = DIFFICULTY_CONFIG[self.difficulty]
        self.q_index += 1
        self.current_time_limit = get_time_for_question(
            self.difficulty, self.q_index - 1
        )
        self._time_left = self.current_time_limit

        # 生成题目
        gen = QuestionGenerator(self.difficulty)
        self.current_question = gen.generate()
        self.question_label.text = self.current_question.text
        self.input_display.text = ""
        self.feedback_label.text = ""
        self._answer_locked = False

        self._update_top_bar()
        self._start_timer()

    def _start_timer(self):
        """启动倒计时"""
        self._stop_timer()
        self.countdown.progress = 1.0
        self._timer_event = Clock.schedule_interval(self._tick, 0.1)

    def _stop_timer(self):
        if self._timer_event:
            self._timer_event.cancel()
            self._timer_event = None

    def _tick(self, dt):
        self._time_left -= dt
        ratio = max(0.0, self._time_left / self.current_time_limit)
        self.countdown.progress = ratio
        if self._time_left <= 0:
            self._handle_timeout()

    def _submit_answer(self):
        """提交当前答案"""
        if self._answer_locked or self.current_question is None:
            return
        text = self.input_display.text.strip()
        if not text:
            return

        try:
            ans = int(text)
        except ValueError:
            self._flash_feedback("请输入数字", COLORS["wrong"])
            return

        self._answer_locked = True
        self._stop_timer()

        if self.current_question.check(ans):
            self._handle_correct()
        else:
            self._handle_wrong(self.current_question.answer)

    def _handle_correct(self):
        cfg = DIFFICULTY_CONFIG[self.difficulty]
        self.score += cfg["score_per_question"]
        self._update_top_bar()

        # 视觉反馈
        self.celebrate.burst()
        self._flash_feedback("你真棒！✨", COLORS["correct"])

        # 语音
        praises = ["你真棒", "太厉害了", "回答正确", "好样的"]
        self.app.tts.speak(random.choice(praises))

        # 0.8 秒后下一题
        Clock.schedule_once(lambda *a: self._next_question(), 0.9)

    def _handle_wrong(self, correct_answer):
        self.wrong_count += 1
        self._update_top_bar()
        self._flash_feedback(f"再想想哦～答案是 {correct_answer}", COLORS["wrong"])
        self.app.tts.speak("再想想")

        if self.wrong_count >= DIFFICULTY_CONFIG[self.difficulty]["max_wrong"]:
            Clock.schedule_once(lambda *a: self._end_game(reason="wrong"), 1.2)
        else:
            self._answer_locked = False  # 允许重试本题
            # 3 秒后自动下一题
            Clock.schedule_once(lambda *a: self._next_question(), 2.5)

    def _handle_timeout(self):
        self.wrong_count += 1
        self._update_top_bar()
        self._answer_locked = True
        self._flash_feedback(
            f"时间到～答案是 {self.current_question.answer}", COLORS["wrong"]
        )
        self.app.tts.speak("时间到")

        if self.wrong_count >= DIFFICULTY_CONFIG[self.difficulty]["max_wrong"]:
            Clock.schedule_once(lambda *a: self._end_game(reason="wrong"), 1.2)
        else:
            Clock.schedule_once(lambda *a: self._next_question(), 2.0)

    def _flash_feedback(self, text, color_hex):
        self.feedback_label.text = text
        self.feedback_label.color = get_color_from_hex(color_hex)
        # 简单弹跳动画
        anim = Animation(font_size=dp(42), duration=0.15) + \
               Animation(font_size=dp(36), duration=0.15)
        anim.start(self.feedback_label)

    def _update_top_bar(self):
        self.score_label.text = f"得分: {self.score}"
        self.progress_label.text = f"题目: {self.q_index}/{self.total_questions}"
        self.wrong_label.text = (
            f"❌: {self.wrong_count}/"
            f"{DIFFICULTY_CONFIG[self.difficulty]['max_wrong']}"
        )

    def _end_game(self, reason="done"):
        self._stop_timer()
        self.question_label.text = ""
        self.input_display.text = ""
        final_score = self.score
        difficulty = self.difficulty
        self.app.end_game(difficulty, final_score)


# ============================================================
# 拍照头像弹窗
# ============================================================
class CameraPopup(Popup):
    """上榜时拍照作为头像"""

    def __init__(self, on_captured, **kwargs):
        super().__init__(**kwargs)
        self.title = "📸 拍照留念"
        self.size_hint = (0.85, 0.75)
        self.on_captured = on_captured

        layout = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))

        try:
            self.camera = Camera(
                resolution=(640, 480),
                play=True,
                size_hint=(1, 0.75),
            )
        except Exception as e:
            self.camera = Label(
                text=f"摄像头不可用:\n{e}",
                font_size=dp(20),
                color=get_color_from_hex(COLORS["wrong"]),
            )
        layout.add_widget(self.camera)

        btn_row = BoxLayout(
            orientation="horizontal", spacing=dp(10), size_hint=(1, 0.15)
        )
        snap_btn = Button(
            text="📷 拍照",
            font_size=dp(22),
            background_color=get_color_from_hex(COLORS["correct"]),
            color=get_color_from_hex(COLORS["text_light"]),
        )
        snap_btn.bind(on_release=self._capture)
        cancel_btn = Button(
            text="跳过",
            font_size=dp(22),
            background_color=get_color_from_hex(COLORS["wrong"]),
            color=get_color_from_hex(COLORS["text_light"]),
        )
        cancel_btn.bind(on_release=lambda *a: self.dismiss())
        btn_row.add_widget(snap_btn)
        btn_row.add_widget(cancel_btn)
        layout.add_widget(btn_row)

        self.add_widget(layout)

    def _capture(self, *args):
        try:
            texture = self.camera.texture
            if texture is None:
                raise RuntimeError("摄像头未就绪")
            # 用时间戳命名
            fname = f"avatar_{int(time.time())}.png"
            fpath = os.path.join(AVATAR_DIR, fname)
            # 导出为 png
            from kivy.core.image import Image as CoreImage
            img = CoreImage(texture)
            img.save(fpath)
            self.on_captured(fpath)
        except Exception as e:
            print(f"[Camera] 拍照失败: {e}")
            self.on_captured(None)
        self.dismiss()


# ============================================================
# 排行榜弹窗
# ============================================================
class LeaderboardPopup(Popup):
    """显示三种难度的排行榜"""

    def __init__(self, leaderboard, **kwargs):
        super().__init__(**kwargs)
        self.title = "🏆 排行榜"
        self.size_hint = (0.8, 0.8)
        self.leaderboard = leaderboard

        self.tab = "easy"
        root = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(15))

        # 难度切换
        tab_row = BoxLayout(size_hint=(1, 0.1), spacing=dp(8))
        self.tab_buttons = {}
        for lv in ("easy", "normal", "hard"):
            btn = Button(
                text=DIFFICULTY_CONFIG[lv]["label"],
                font_size=dp(18),
                background_color=get_color_from_hex(COLORS["button"]),
                color=get_color_from_hex(COLORS["text_light"]),
            )
            btn.bind(on_release=lambda inst, l=lv: self._switch_tab(l))
            self.tab_buttons[lv] = btn
            tab_row.add_widget(btn)
        root.add_widget(tab_row)

        # 列表
        from kivy.uix.scrollview import ScrollView
        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.list_layout = BoxLayout(
            orientation="vertical", spacing=dp(6), size_hint_y=None
        )
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.scroll.add_widget(self.list_layout)
        root.add_widget(self.scroll)

        # 关闭
        close_btn = Button(
            text="关闭",
            font_size=dp(20),
            background_color=get_color_from_hex(COLORS["text"]),
            color=get_color_from_hex(COLORS["text_light"]),
            size_hint=(0.4, 0.1),
            pos_hint={"center_x": 0.5},
        )
        close_btn.bind(on_release=lambda *a: self.dismiss())
        root.add_widget(close_btn)

        self.add_widget(root)
        self._switch_tab("easy")

    def _switch_tab(self, level):
        self.tab = level
        for lv, btn in self.tab_buttons.items():
            btn.background_color = get_color_from_hex(
                COLORS["button_press"] if lv == level else COLORS["button"]
            )
        self._refresh_list()

    def _refresh_list(self):
        self.list_layout.clear_widgets()
        entries = self.leaderboard.get(self.tab)
        if not entries:
            self.list_layout.add_widget(Label(
                text="暂无记录，快来挑战吧！",
                font_size=dp(20),
                color=get_color_from_hex(COLORS["text"]),
            ))
            return
        for i, e in enumerate(entries):
            row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
            # 头像
            if e.get("avatar") and os.path.exists(e["avatar"]):
                img = Image(
                    source=e["avatar"],
                    size_hint=(None, None),
                    size=(dp(40), dp(40)),
                    allow_stretch=True,
                    keep_ratio=True,
                )
            else:
                img = Label(
                    text="😊",
                    font_size=dp(28),
                    size_hint=(None, None),
                    size=(dp(40), dp(40)),
                )
            row.add_widget(img)

            info = Label(
                text=f"#{i+1}  {e['name']}  ——  {e['score']} 分  ({e.get('date','')})",
                font_size=dp(20),
                color=get_color_from_hex(COLORS["text"]),
                halign="left",
            )
            row.add_widget(info)
            self.list_layout.add_widget(row)


# ============================================================
# 游戏结束弹窗
# ============================================================
class GameOverPopup(Popup):
    """游戏结束：显示得分、上榜提示、输入名字、拍照"""

    def __init__(self, difficulty, score, leaderboard, on_restart, **kwargs):
        super().__init__(**kwargs)
        self.title = "游戏结束"
        self.size_hint = (0.75, 0.6)
        self.difficulty = difficulty
        self.score = score
        self.leaderboard = leaderboard
        self.on_restart = on_restart

        layout = BoxLayout(orientation="vertical", spacing=dp(15), padding=dp(20))

        self.info_label = Label(
            text="",
            font_size=dp(26),
            color=get_color_from_hex(COLORS["text"]),
        )
        layout.add_widget(self.info_label)

        # 名字输入
        self.name_input = TextInput(
            hint_text="输入你的名字",
            font_size=dp(24),
            size_hint=(0.8, 0.18),
            pos_hint={"center_x": 0.5},
            halign="center",
            multiline=False,
        )
        layout.add_widget(self.name_input)

        # 按钮行
        btn_row = BoxLayout(
            orientation="horizontal", spacing=dp(12), size_hint=(1, 0.2)
        )
        self.save_btn = Button(
            text="保存成绩",
            font_size=dp(20),
            background_color=get_color_from_hex(COLORS["correct"]),
            color=get_color_from_hex(COLORS["text_light"]),
        )
        self.save_btn.bind(on_release=self._on_save)
        self.skip_btn = Button(
            text="不用了",
            font_size=dp(20),
            background_color=get_color_from_hex(COLORS["wrong"]),
            color=get_color_from_hex(COLORS["text_light"]),
        )
        self.skip_btn.bind(on_release=lambda *a: self.dismiss())
        btn_row.add_widget(self.save_btn)
        btn_row.add_widget(self.skip_btn)
        layout.add_widget(btn_row)

        self.add_widget(layout)

        self._check_board()

    def _check_board(self):
        on_board = self.leaderboard.is_on_board(self.difficulty, self.score)
        if on_board:
            self.info_label.text = (
                f"🎉 太棒了！得分 {self.score}\n恭喜上榜！输入名字拍照留念吧"
            )
            self.info_label.color = get_color_from_hex(COLORS["accent"])
        else:
            self.info_label.text = (
                f"本次得分: {self.score}\n再加把劲，下次上榜！"
            )
            self.info_label.color = get_color_from_hex(COLORS["text"])

    def _on_save(self, *args):
        name = self.name_input.text.strip() or "小玩家"
        # 检查是否上榜
        on_board = self.leaderboard.is_on_board(self.difficulty, self.score)
        if on_board:
            # 打开拍照
            def after_photo(path):
                rank, _ = self.leaderboard.add(
                    self.difficulty, name, self.score, avatar_path=path
                )
                self.dismiss()
                self.on_restart()

            popup = CameraPopup(on_captured=after_photo)
            popup.open()
        else:
            self.leaderboard.add(self.difficulty, name, self.score)
            self.dismiss()
            self.on_restart()


# ============================================================
# 主 App
# ============================================================
class KidsMathApp(App):
    """Kivy 应用入口"""

    def build(self):
        self.title = "数学小天才"
        self.root_layout = FloatLayout()

        # 核心模块
        self.leaderboard = Leaderboard()
        self.tts = TTS()
        self.voice = VoiceRecognizer()

        # 界面
        self.difficulty_screen = DifficultyScreen(app_ref=self)
        self.game_screen = GameScreen(app_ref=self)

        self.root_layout.add_widget(self.difficulty_screen)
        return self.root_layout

    # ---- 界面切换 ----
    def start_game(self, difficulty):
        self.root_layout.clear_widgets()
        self.game_screen = GameScreen(app_ref=self)
        self.root_layout.add_widget(self.game_screen)
        self.game_screen.start_game(difficulty)
        # 启动语音监听
        if self.voice.available:
            self.voice.start_listening()
            Clock.schedule_interval(self._poll_voice, 0.3)

    def exit_to_menu(self):
        self._cleanup_game()
        self.root_layout.clear_widgets()
        self.difficulty_screen = DifficultyScreen(app_ref=self)
        self.root_layout.add_widget(self.difficulty_screen)

    def end_game(self, difficulty, score):
        self._cleanup_game()
        popup = GameOverPopup(
            difficulty=difficulty,
            score=score,
            leaderboard=self.leaderboard,
            on_restart=self.exit_to_menu,
        )
        popup.open()

    def show_leaderboard(self):
        popup = LeaderboardPopup(leaderboard=self.leaderboard)
        popup.open()

    # ---- 语音轮询 ----
    def _poll_voice(self, dt):
        text = self.voice.poll_text(timeout=0)
        if not text:
            return
        print(f"[App] 语音输入: {text}")

        # 在等待开始阶段，识别到"开始"就开局
        if "开始" in text and hasattr(self.game_screen, "_begin_first_question"):
            # 仅当游戏屏处于等待状态时
            if self.game_screen.feedback_label.text and "说" in self.game_screen.feedback_label.text:
                self.game_screen._begin_first_question()
                return

        # 游戏中：识别数字作为答案
        if self.game_screen.current_question and not self.game_screen._answer_locked:
            num = self.voice.extract_number(text)
            if num is not None:
                self.game_screen.input_display.text = str(num)
                self.game_screen._submit_answer()

    def _cleanup_game(self):
        Clock.unschedule(self._poll_voice)
        if self.voice:
            self.voice.stop_listening()

    def on_stop(self):
        if self.voice:
            self.voice.close()
        if self.tts:
            self.tts.shutdown()
        return super().on_stop()


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    KidsMathApp().run()
