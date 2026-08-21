"""
voice.py —— 离线语音识别

桌面端：
    麦克风 -> PyAudio -> Vosk

Android：
    麦克风 -> Android AudioRecord -> PyJNIus -> Vosk

识别“开始”和数字（零~一百等）。
"""

import os
import json
import threading
import queue
import re

from config import APP_DIR


# ============================================================
# 平台判断
# ============================================================

try:
    from kivy.utils import platform
except Exception:
    platform = "unknown"

IS_ANDROID = platform == "android"


# ============================================================
# Vosk
# ============================================================

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    Model = None
    KaldiRecognizer = None
    VOSK_AVAILABLE = False


# ============================================================
# PyAudio
# 只在桌面端使用
# Android 不使用 PyAudio
# ============================================================

if not IS_ANDROID:
    try:
        import pyaudio
        PYAUDIO_AVAILABLE = True
    except ImportError:
        pyaudio = None
        PYAUDIO_AVAILABLE = False
else:
    pyaudio = None
    PYAUDIO_AVAILABLE = False


# ============================================================
# Vosk 中文模型目录
# ============================================================

# GitHub Actions 下载：
# vosk-model-small-cn-0.22.zip
# 并重命名为 model-zh
MODEL_DIR = os.path.join(APP_DIR, "model-zh")


class VoiceRecognizer:
    """
    离线语音识别器。

    使用方式：
        voice = VoiceRecognizer()
        voice.start_listening()

        text = voice.poll_text()
        number = voice.poll_number()

        voice.close()
    """

    SAMPLE_RATE = 16000

    # PyAudio 每次读取的采样点数量
    DESKTOP_FRAMES = 4096

    # Android 一次读取的字节数量
    # PCM16 = 每个采样点 2 字节
    ANDROID_BUFFER_BYTES = 8192

    def __init__(self, model_dir=MODEL_DIR):

        self.model_dir = model_dir

        self.model = None
        self.recognizer = None

        # 桌面 PyAudio
        self.audio = None
        self.stream = None

        # Android AudioRecord
        self.android_record = None
        self.android_buffer_size = self.ANDROID_BUFFER_BYTES

        self._use_pyaudio = False
        self._use_android_audio = False

        # 识别结果队列
        self.result_queue = queue.Queue()

        # 后台线程
        self._stop_event = threading.Event()
        self._thread = None

        self.available = False

        # ----------------------------------------------------
        # 检查 Vosk
        # ----------------------------------------------------

        if not VOSK_AVAILABLE:
            print("[Voice] Vosk 未安装，语音功能不可用")
            return

        # ----------------------------------------------------
        # 检查模型
        # ----------------------------------------------------

        if not os.path.isdir(self.model_dir):
            print(f"[Voice] 模型目录不存在: {self.model_dir}")
            print("[Voice] 请确认 model-zh 已被打包进 APK")
            return

        try:

            print(f"[Voice] 正在加载模型: {self.model_dir}")

            self.model = Model(self.model_dir)

            self.recognizer = KaldiRecognizer(
                self.model,
                self.SAMPLE_RATE
            )

            self.recognizer.SetWords(False)

            # ====================================================
            # Android
            # ====================================================

            if IS_ANDROID:

                try:
                    from jnius import autoclass

                    # 这里只检查 PyJNIus 是否可用
                    autoclass("android.media.AudioRecord")

                    self._use_android_audio = True
                    self._use_pyaudio = False

                    self.available = True

                    print(
                        "[Voice] Android 模式初始化成功 "
                        "(AudioRecord + Vosk)"
                    )

                except Exception as e:

                    print(
                        f"[Voice] Android AudioRecord "
                        f"初始化准备失败: {e}"
                    )

                    self.available = False

            # ====================================================
            # Windows/Linux/macOS
            # ====================================================

            else:

                if not PYAUDIO_AVAILABLE:
                    print(
                        "[Voice] 桌面端未安装 PyAudio，"
                        "语音功能不可用"
                    )
                    self.available = False
                    return

                self.audio = pyaudio.PyAudio()

                self.stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=self.DESKTOP_FRAMES,
                )

                self._use_pyaudio = True
                self._use_android_audio = False
                self.available = True

                print(
                    "[Voice] 桌面模式初始化成功 "
                    "(PyAudio + Vosk)"
                )

        except Exception as e:

            print(f"[Voice] 初始化失败: {e}")

            self.available = False

    # ============================================================
    # 中文数字解析
    # ============================================================

    CN_DIGITS = {
        "零": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
        "百": 100,
        "千": 1000,
    }

    @classmethod
    def cn_number_to_int(cls, text):
        """
        中文数字转整数。

        示例：
            一      -> 1
            十      -> 10
            十二    -> 12
            二十    -> 20
            二十三  -> 23
            一百    -> 100
        """

        text = text.strip()

        if not text:
            return None

        # ------------------------------
        # 阿拉伯数字
        # ------------------------------

        try:
            value = int(text)

            if 0 <= value <= 1000:
                return value

            return None

        except ValueError:
            pass

        # ------------------------------
        # 简单中文数字
        # ------------------------------

        digit_map = {
            "零": 0,
            "一": 1,
            "二": 2,
            "两": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
        }

        # 一百以内
        if "百" not in text:

            if "十" in text:

                parts = text.split("十")

                # 十、十二
                if parts[0] == "":
                    tens = 1
                else:
                    tens = digit_map.get(parts[0])

                if tens is None:
                    return None

                result = tens * 10

                if len(parts) > 1 and parts[1]:
                    ones = digit_map.get(parts[1])

                    if ones is None:
                        return None

                    result += ones

                if 0 <= result <= 1000:
                    return result

                return None

            # 单个数字
            if len(text) == 1:
                return digit_map.get(text)

        # ------------------------------
        # 一百到九百九十九
        # ------------------------------

        if "百" in text:

            parts = text.split("百", 1)

            if parts[0] == "":
                hundreds = 1
            else:
                hundreds = digit_map.get(parts[0])

            if hundreds is None:
                return None

            result = hundreds * 100

            rest = parts[1]

            if not rest:
                return result

            # 一百零三
            if rest.startswith("零"):
                rest = rest[1:]

                if not rest:
                    return result

            if "十" in rest:

                parts2 = rest.split("十", 1)

                if parts2[0] == "":
                    tens = 1
                else:
                    tens = digit_map.get(parts2[0])

                if tens is None:
                    return None

                result += tens * 10

                if parts2[1]:

                    ones = digit_map.get(parts2[1])

                    if ones is None:
                        return None

                    result += ones

            else:

                ones = digit_map.get(rest)

                if ones is None:
                    return None

                result += ones

            if 0 <= result <= 1000:
                return result

        return None

    @classmethod
    def extract_number(cls, text):
        """
        从识别文本里提取数字。
        """

        if not text:
            return None

        # 阿拉伯数字
        m = re.search(r"\d+", text)

        if m:
            return int(m.group())

        # Vosk 有时会在中文字之间加入空格
        # 例如：
        #   "二 十 三"
        # 先把空格去掉
        clean_text = text.replace(" ", "")

        # 只提取中文数字字符
        m = re.search(
            r"[零一二两三四五六七八九十百]+",
            clean_text
        )

        if not m:
            return None

        return cls.cn_number_to_int(m.group())

    # ============================================================
    # 启动监听
    # ============================================================

    def start_listening(self):
        """
        开始监听。

        Android：
            第一次会请求 RECORD_AUDIO 权限。

        桌面：
            直接使用 PyAudio。
        """

        if not self.available:
            print("[Voice] 当前语音识别器不可用")
            return False

        if self._thread and self._thread.is_alive():
            return True

        # ========================================================
        # Android 权限
        # ========================================================

        if IS_ANDROID:

            try:

                from android.permissions import (
                    Permission,
                    check_permission,
                    request_permissions,
                )

                # 已授权
                if check_permission(Permission.RECORD_AUDIO):

                    print("[Voice] 麦克风权限已获得")

                    return self._start_thread()

                # 尚未授权
                print("[Voice] 正在请求麦克风权限...")

                request_permissions(
                    [Permission.RECORD_AUDIO],
                    self._on_permission_result
                )

                # 请求已成功发出
                return True

            except Exception as e:

                print(
                    f"[Voice] 请求麦克风权限失败: {e}"
                )

                return False

        # ========================================================
        # 桌面
        # ========================================================

        return self._start_thread()

    def _on_permission_result(
        self,
        permissions,
        grant_results
    ):
        """
        Android 权限请求完成后的回调。
        """

        try:

            granted = (
                bool(grant_results)
                and all(grant_results)
            )

            if granted:

                print("[Voice] 用户已允许麦克风权限")

                self._start_thread()

            else:

                print("[Voice] 用户拒绝麦克风权限")

        except Exception as e:

            print(
                f"[Voice] 权限回调异常: {e}"
            )

    def _start_thread(self):
        """
        真正启动后台录音线程。
        """

        if self._thread and self._thread.is_alive():
            return True

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="VoiceRecognizer"
        )

        self._thread.start()

        return True

    # ============================================================
    # 停止监听
    # ============================================================

    def stop_listening(self):
        """
        停止后台监听。
        """

        self._stop_event.set()

        if self._thread:

            self._thread.join(timeout=1.5)

        self._thread = None

    # ============================================================
    # Android AudioRecord
    # ============================================================

    def _create_android_recorder(self):
        """
        创建 Android 原生 AudioRecord。
        """

        from jnius import autoclass

        AudioRecord = autoclass(
            "android.media.AudioRecord"
        )

        AudioFormat = autoclass(
            "android.media.AudioFormat"
        )

        AudioSource = autoclass(
            "android.media.MediaRecorder$AudioSource"
        )

        channel_config = (
            AudioFormat.CHANNEL_IN_MONO
        )

        audio_format = (
            AudioFormat.ENCODING_PCM_16BIT
        )

        min_buffer = AudioRecord.getMinBufferSize(
            self.SAMPLE_RATE,
            channel_config,
            audio_format
        )

        if min_buffer <= 0:
            raise RuntimeError(
                f"AudioRecord getMinBufferSize "
                f"失败: {min_buffer}"
            )

        self.android_buffer_size = max(
            min_buffer,
            self.ANDROID_BUFFER_BYTES
        )

        print(
            "[Voice] Android AudioRecord buffer = "
            f"{self.android_buffer_size} bytes"
        )

        self.android_record = AudioRecord(
            AudioSource.MIC,
            self.SAMPLE_RATE,
            channel_config,
            audio_format,
            self.android_buffer_size
        )

        # STATE_INITIALIZED == 1
        if (
            self.android_record.getState()
            != AudioRecord.STATE_INITIALIZED
        ):

            try:
                self.android_record.release()
            except Exception:
                pass

            self.android_record = None

            raise RuntimeError(
                "AudioRecord 初始化失败"
            )

    # ============================================================
    # 后台监听
    # ============================================================

    def _listen_loop(self):

        # ========================================================
        # Android AudioRecord
        # ========================================================

        if self._use_android_audio:

            self._listen_loop_android()

            return

        # ========================================================
        # Desktop PyAudio
        # ========================================================

        if self._use_pyaudio:

            self._listen_loop_pyaudio()

            return

        print("[Voice] 没有可用的录音后端")

    def _listen_loop_pyaudio(self):
        """
        Windows/Linux 桌面录音。
        """

        print("[Voice] PyAudio 开始监听")

        while not self._stop_event.is_set():

            try:

                data = self.stream.read(
                    self.DESKTOP_FRAMES,
                    exception_on_overflow=False
                )

                self._process_audio(data)

            except Exception as e:

                print(
                    f"[Voice] PyAudio 识别异常: {e}"
                )

                break

        print("[Voice] PyAudio 停止监听")

    def _listen_loop_android(self):
        """
        Android 原生 AudioRecord 录音。
        """

        try:

            self._create_android_recorder()

            self.android_record.startRecording()

            print(
                "[Voice] Android AudioRecord 开始监听"
            )

            # PyJNIus 支持将 Python bytearray
            # 传入 Java byte[] 参数。
            buffer = bytearray(
                self.android_buffer_size
            )

            while not self._stop_event.is_set():

                size = self.android_record.read(
                    buffer,
                    0,
                    len(buffer)
                )

                if size > 0:

                    data = bytes(
                        buffer[:size]
                    )

                    self._process_audio(data)

                elif size < 0:

                    print(
                        "[Voice] AudioRecord.read "
                        f"返回错误码: {size}"
                    )

        except Exception as e:

            print(
                f"[Voice] Android 录音异常: {e}"
            )

        finally:

            self._release_android_recorder()

            print(
                "[Voice] Android AudioRecord 停止监听"
            )

    # ============================================================
    # Vosk 识别
    # ============================================================

    def _process_audio(self, data):
        """
        把 PCM16 音频送入 Vosk。
        """

        if not data:
            return

        try:

            if self.recognizer.AcceptWaveform(data):

                result = json.loads(
                    self.recognizer.Result()
                )

                text = (
                    result
                    .get("text", "")
                    .strip()
                )

                if text:

                    self.result_queue.put(text)

                    print(
                        f"[Voice] 识别: {text}"
                    )

        except Exception as e:

            print(
                f"[Voice] Vosk 处理异常: {e}"
            )

    # ============================================================
    # 获取识别结果
    # ============================================================

    def poll_text(self, timeout=0):
        """
        非阻塞获取一条识别文本。
        """

        try:

            return self.result_queue.get(
                timeout=timeout
            )

        except queue.Empty:

            return None

    def poll_number(self, timeout=0):
        """
        获取识别结果并转换为数字。
        """

        text = self.poll_text(
            timeout=timeout
        )

        if text is None:
            return None

        return self.extract_number(text)

    # ============================================================
    # Android 资源释放
    # ============================================================

    def _release_android_recorder(self):

        if self.android_record is None:
            return

        try:
            self.android_record.stop()
        except Exception:
            pass

        try:
            self.android_record.release()
        except Exception:
            pass

        self.android_record = None

    # ============================================================
    # 总资源释放
    # ============================================================

    def close(self):

        self.stop_listening()

        # Android
        self._release_android_recorder()

        # Desktop PyAudio
        try:

            if self.stream:

                self.stream.stop_stream()
                self.stream.close()

        except Exception:
            pass

        try:

            if self.audio:

                self.audio.terminate()

        except Exception:
            pass

        self.stream = None
        self.audio = None

        self.available = False

        print("[Voice] 语音识别资源已释放")
