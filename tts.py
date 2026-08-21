"""
tts.py —— 语音播报（"准备好了请说开始"、"你真棒"等）
Android 上优先使用系统 TTS，桌面端用 pyttsx3 或 gTTS 兜底
"""

import platform
import threading

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Android 上可用 jnius 调用系统 TextToSpeech
try:
    from jnius import autoclass
    ANDROID_TTS = True
except ImportError:
    ANDROID_TTS = False


class TTS:
    """跨平台文本转语音"""

    def __init__(self):
        self.engine = None
        self._android_tts = None
        self._lock = threading.Lock()

        if ANDROID_TTS:
            self._init_android()
        elif PYTTSX3_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                # 尝试设置中文
                try:
                    voices = self.engine.getProperty("voices")
                    for v in voices:
                        if "zh" in v.id.lower() or "chinese" in v.name.lower():
                            self.engine.setProperty("voice", v.id)
                            break
                except Exception:
                    pass
                self.engine.setProperty("rate", 180)
            except Exception as e:
                print(f"[TTS] pyttsx3 初始化失败: {e}")
                self.engine = None

    def _init_android(self):
        try:
            Locale = autoclass("java.util.Locale")
            TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity

            def on_init(status):
                self._android_tts.setLanguage(Locale.CHINESE)

            self._android_tts = TextToSpeech(activity, on_init)
        except Exception as e:
            print(f"[TTS] Android TTS 初始化失败: {e}")
            self._android_tts = None

    def speak(self, text):
        """异步播报文本"""
        threading.Thread(target=self._speak_block, args=(text,), daemon=True).start()

    def _speak_block(self, text):
        with self._lock:
            try:
                if self._android_tts:
                    self._android_tts.speak(text, 0, None, None)
                elif self.engine:
                    self.engine.say(text)
                    self.engine.runAndWait()
            except Exception as e:
                print(f"[TTS] 播报失败: {e}")

    def shutdown(self):
        try:
            if self._android_tts:
                self._android_tts.shutdown()
            elif self.engine:
                self.engine.stop()
        except Exception:
            pass
