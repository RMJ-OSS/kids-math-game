"""
leaderboard.py —— 本地排行榜（JSON 存储，每种难度前 10 名）
"""

import json
import os
import time
from config import LEADERBOARD_FILE, MAX_LEADERBOARD


class Leaderboard:
    """管理三种难度的排行榜"""

    def __init__(self):
        self.data = self._load()

    def _load(self):
        if not os.path.exists(LEADERBOARD_FILE):
            return {"easy": [], "normal": [], "hard": []}
        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            # 兼容旧格式
            for k in ("easy", "normal", "hard"):
                d.setdefault(k, [])
            return d
        except (json.JSONDecodeError, OSError):
            return {"easy": [], "normal": [], "hard": []}

    def _save(self):
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add(self, difficulty, name, score, avatar_path=None):
        """
        添加一条记录。返回 (rank, is_new_record)
        rank: 1-based 排名；is_new_record: 是否打破了之前的最佳
        """
        entry = {
            "name": name,
            "score": int(score),
            "avatar": avatar_path,
            "date": time.strftime("%Y-%m-%d %H:%M"),
        }
        lst = self.data.setdefault(difficulty, [])
        prev_best = max((e["score"] for e in lst), default=0)

        lst.append(entry)
        lst.sort(key=lambda e: e["score"], reverse=True)
        lst[:] = lst[:MAX_LEADERBOARD]  # 只保留前 N 名

        new_best = max((e["score"] for e in lst), default=0)
        rank = next((i + 1 for i, e in enumerate(lst) if e is entry), None)
        if rank is None:
            # entry 可能被截断（不在前10）
            rank = MAX_LEADERBOARD + 1

        self._save()
        return rank, (new_best > prev_best)

    def get(self, difficulty):
        return list(self.data.get(difficulty, []))

    def is_on_board(self, difficulty, score):
        """分数是否能上榜"""
        lst = self.data.get(difficulty, [])
        if len(lst) < MAX_LEADERBOARD:
            return True
        return score > min(e["score"] for e in lst)
