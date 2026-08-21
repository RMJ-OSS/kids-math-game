"""
question_generator.py —— 随机出题，保证结果在 0-100 以内
"""

import random
import operator

from config import DIFFICULTY_CONFIG


class Question:
    """一道题目的数据类"""

    def __init__(self, a, b, op):
        self.a = a
        self.b = b
        self.op = op
        self.text = f"{a} {op} {b} = ?"
        self.answer = self._compute(a, b, op)

    @staticmethod
    def _compute(a, b, op):
        ops = {
            "+": operator.add,
            "-": operator.sub,
            "×": operator.mul,
            "÷": operator.truediv,
        }
        return ops[op](a, b)

    def check(self, value):
        """判断答案是否正确（允许浮点误差）"""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False
        if self.op == "÷":
            return abs(v - self.answer) < 0.001
        return int(v) == int(self.answer)


class QuestionGenerator:
    """按难度生成题目"""

    def __init__(self, difficulty="easy"):
        if difficulty not in DIFFICULTY_CONFIG:
            raise ValueError(f"未知难度: {difficulty}")
        self.difficulty = difficulty
        self.cfg = DIFFICULTY_CONFIG[difficulty]

    def generate(self):
        """生成一道合法题目（最多重试 200 次）"""
        ops = self.cfg["ops"]
        max_op = self.cfg["max_operand"]
        max_result = 100  # 全局限制

        for _ in range(200):
            op = random.choice(ops)
            a = random.randint(1, max_op)
            b = random.randint(1, max_op)

            if op == "+":
                if a + b <= max_result:
                    return Question(a, b, "+")
            elif op == "-":
                if a >= b and a - b <= max_result:
                    return Question(a, b, "-")
            elif op == "×":
                if a * b <= max_result:
                    return Question(a, b, "×")
            elif op == "÷":
                # 保证整除，且商在范围内
                if b != 0 and a * b <= max_result:
                    # 用 a*b 作为被除数，b 作为除数，商为 a
                    dividend = a * b
                    if dividend <= max_result:
                        return Question(dividend, b, "÷")

        # 极端情况兜底：一道简单加法
        return Question(random.randint(1, 10), random.randint(1, 10), "+")
