"""
voice.py —— 离线语音识别
使用 Vosk 中文模型，识别"开始"和数字（零~一百）
Android 上通过 Buildozer 打包 vosk 即可工作。
"""

import os
import json
import threading
import queue

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

# pyaudio 仅在桌面环境可用，Android 上用 Audiostream 替代
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

from config import APP_DIR

# Vosk 中文模型路径
# 本地开发：请手动下载并解压到项目根目录下的 model-zh/
# GitHub Actions：工作流会下载 vosk-model-small-zh-cn-0.22 并软链/重命名为 model-zh
MODEL_DIR = os.path.join(APP_DIR, "model-zh")


class VoiceRecognizer:
    """
    离线语音识别器。
    - 监听麦克风
    - 把识别到的文本放入 self.result_queue
    - 调用者用 poll_text() 取走
    """

    def __init__(self, model_dir=MODEL_DIR):
        self.model_dir = model_dir
        self.model = None
        self.recognizer = None
        self.audio = None
        self.stream = None
        self.result_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        self.available = False

        if not VOSK_AVAILABLE:
            print("[Voice] Vosk/PyAudio 未安装，语音功能不可用")
            return

        if not os.path.isdir(self.model_dir):
            print(f"[Voice] 模型目录不存在: {self.model_dir}")
            print("[Voice] 请下载 https://alphacephei.com/vosk/models "
                  "并解压到项目根目录")
            return

        try:
            self.model = Model(self.model_dir)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            self.recognizer.SetWords(False)

            # 桌面环境用 pyaudio；Android 上 pyaudio 不可用，
            # 由 Kivy 的 audiostream 提供音频输入（由调用方注入）
            if PYAUDIO_AVAILABLE:
                self.audio = pyaudio.PyAudio()
                self.stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=4096,
                )
                self._use_pyaudio = True
            else:
                self.audio = None
                self.stream = None
                self._use_pyaudio = False

            self.available = True
            print("[Voice] 初始化成功，离线中文模型已加载")
        except Exception as e:
            print(f"[Voice] 初始化失败: {e}")
            self.available = False

    # ---------- 中文数字解析 ----------
    CN_DIGITS = {
        "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
        "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
        "百": 100, "千": 1000,
    }

    @classmethod
    def cn_number_to_int(cls, text):
        """
        把中文数字串解析成整数，例如 "二十三" -> 23
        支持 0-100 范围
        """
        text = text.strip()
        if not text:
            return None

        # 先尝试直接阿拉伯数字
        try:
            return int(text)
        except ValueError:
            pass

        # 中文解析
        result = 0
        section = 0  # 当前十进段
        for ch in text:
            if ch in ("零",):
                continue
            if ch in ("一", "二", "两", "三", "四", "五", "六", "七", "八", "九"):
                section += cls.CN_DIGITS[ch]
            elif ch == "十":
                if section == 0:
                    section = 10
                else:
                    section *= 10
            elif ch == "百":
                if section == 0:
                    section = 100
                else:
                    section *= 100
        result += section

        if 0 <= result <= 1000:
            return result
        return None

    @classmethod
    def extract_number(cls, text):
        """从一段识别文本里提取第一个数字（阿拉伯或中文）"""
        if not text:
            return None
        # 优先匹配阿拉伯数字
        import re
        m = re.search(r"\d+", text)
        if m:
            return int(m.group())
        # 否则尝试中文
        return cls.cn_number_to_int(text)

    # ---------- 后台监听 ----------
    def start_listening(self):
        """启动后台监听线程"""
        if not self.available:
            return False
        if self._thread and self._thread.is_alive():
            return True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        return True

    def stop_listening(self):
        """停止后台监听"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)

    def _listen_loop(self):
        while not self._stop_event.is_set():
            try:
                data = self.stream.read(4096, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        self.result_queue.put(text)
                        print(f"[Voice] 识别: {text}")
            except Exception as e:
                print(f"[Voice] 识别异常: {e}")
                break

    def poll_text(self, timeout=0):
        """
        非阻塞取一条识别文本，返回字符串或 None
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def poll_number(self, timeout=0):
        """取一条识别结果并解析为数字"""
        text = self.poll_text(timeout=timeout)
        if text is None:
            return None
        return self.extract_number(text)

    # ---------- 资源释放 ----------
    def close(self):
        self.stop_listening()
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.audio:
                self.audio.terminate()
        except Exception:
            pass
        self.available = False
