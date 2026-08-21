"""
config.py —— 全局配置：难度参数、颜色、路径等
"""

import os
import json

# ============================================================
# 路径
# ============================================================
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
LEADERBOARD_FILE = os.path.join(DATA_DIR, "leaderboard.json")
AVATAR_DIR = os.path.join(DATA_DIR, "avatars")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(AVATAR_DIR, exist_ok=True)

# ============================================================
# 难度配置
# ============================================================
DIFFICULTY_CONFIG = {
    "easy": {
        "label": "简单 (3-6岁)",
        "base_time": 20,        # 首题倒计时(秒)
        "min_time": 8,          # 最低倒计时底线(秒)
        "time_decay": 0.3,      # 每题减少秒数
        "max_wrong": 5,         # 允许错误/超时次数
        "total_questions": 15,   # 总题数
        "score_per_question": 10,
        "ops": ["+", "-"],      # 仅加减
        "max_operand": 20,      # 操作数上限
        "age_range": "3-6岁",
    },
    "normal": {
        "label": "普通 (6-9岁)",
        "base_time": 15,
        "min_time": 5,
        "time_decay": 0.4,
        "max_wrong": 4,
        "total_questions": 20,
        "score_per_question": 20,
        "ops": ["+", "-", "×"], # 加减乘
        "max_operand": 50,
        "age_range": "6-9岁",
    },
    "hard": {
        "label": "困难 (9-12岁)",
        "base_time": 12,
        "min_time": 4,
        "time_decay": 0.5,
        "max_wrong": 3,
        "total_questions": 25,
        "score_per_question": 30,
        "ops": ["+", "-", "×", "÷"], # 加减乘除
        "max_operand": 100,
        "age_range": "9-12岁",
    },
}

# ============================================================
# 颜色主题（明亮、儿童友好）
# ============================================================
COLORS = {
    "bg":              "#F0F8FF",   # 爱丽丝蓝
    "primary":         "#FF6B6B",   # 珊瑚红
    "secondary":       "#4ECDC4",   # 薄荷绿
    "accent":          "#FFD93D",   # 阳光黄
    "text":            "#2C3E50",   # 深蓝灰
    "text_light":      "#FFFFFF",
    "correct":         "#27AE60",   # 翠绿
    "wrong":           "#E74C3C",   # 红
    "timer_ring":      "#3498DB",   # 蓝
    "timer_warning":   "#E67E22",   # 橙
    "timer_danger":    "#E74C3C",   # 红
    "button":          "#5DADE2",   # 天蓝
    "button_press":    "#2E86C1",   # 深天蓝
    "celebrate":       "#F39C12",   # 庆祝金
    "purple":          "#9B59B6",
    "pink":            "#E91E63",
    "orange":          "#FF9800",
}

# ============================================================
# 排行榜
# ============================================================
MAX_LEADERBOARD = 10  # 每种难度保存前10名

# ============================================================
# 倒计时递减公式
# ============================================================
def get_time_for_question(difficulty, question_index):
    """根据题号计算当前倒计时，不低于最低底线"""
    cfg = DIFFICULTY_CONFIG[difficulty]
    t = cfg["base_time"] - question_index * cfg["time_decay"]
    return max(t, cfg["min_time"])
