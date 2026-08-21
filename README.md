# 🌈 数学小天才 — Kivy + Buildozer 平板 App 打包文档

> 一份面向家长的完整指南：从零开始，把"数学小天才"打包成可在华为/安卓平板上安装的 `.apk` 文件。

---

## 一、功能回顾

| # | 功能 | 实现 |
|---|------|------|
| 1 | 随机加减乘除，结果 0-100 | `QuestionGenerator` 类，200 次重试保证合法 |
| 2 | 简单 / 普通 / 困难 三档 | `config.py` 中 `DIFFICULTY_CONFIG` 字典 |
| 3 | 屏幕中央题目 + 倒计时圆环 | Kivy `CountdownRing` 自定义 Widget |
| 4 | 答错/超时 N 次结束 | `wrong_count` 计数，达上限自动结束 |
| 5 | 本地语音识别（数字 + "开始"） | Vosk 离线中文模型，无需联网 |
| 6 | 分龄：3-6 / 6-9 / 9-12 | 简单仅加减，普通加乘，困难全四则 |
| 7 | 积分 + 本地排行榜前 10 | JSON 存储，上榜可拍照 |
| 8 | 语音提示"准备好了请说开始" | TTS 播报 + 界面提示，支持点击备选 |
| 9 | 答对撒花 + "你真棒" | 80 粒子 Canvas 动画 + TTS |
| 10 | 倒计时随题数递减但有底线 | `max(base - n*decay, min_time)` |

---

## 二、环境准备

### 2.1 硬件要求

- 一台电脑（**推荐 Ubuntu 22.04 / macOS**，Windows 用 WSL2）
- 一台华为/安卓平板（开启 USB 调试）
- USB 数据线

### 2.2 软件安装（Ubuntu / WSL2）

```bash
# 1. 系统依赖
sudo apt update
sudo apt install -y \
    git zip unzip openjdk-17-jdk python3-pip python3-venv \
    libffi-dev libssl-dev build-essential \
    zlib1g-dev libbz2-dev libsqlite3-dev \
    libx11-dev libxext-dev libxrender-dev \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    ffmpeg

# 2. 创建虚拟环境（强烈推荐）
python3 -m venv venv
source venv/bin/activate

# 3. 升级 pip
pip install --upgrade pip wheel setuptools Cython

# 4. 安装 Kivy（桌面调试用）
pip install "kivy[base]"

# 5. 安装 Buildozer
pip install buildozer
```

> **WSL2 注意**：Buildozer 需要在 Linux 环境下运行。WSL2 可以直接用，但首次构建会下载约 1-3GB 的 Android SDK/NDK，请确保磁盘空间充足。

### 2.3 下载 Vosk 中文模型

语音识别使用 **Vosk 离线中文模型**（约 40MB，无需联网）：

```bash
cd /path/to/kids_math_kivy
wget https://alphacephei.com/vosk/models/vosk-model-small-zh-cn-0.22.zip
unzip vosk-model-small-zh-cn-0.22.zip
# 解压后目录名应为: vosk-model-small-zh-cn-0.22
```

目录结构应如下：
```
kids_math_kivy/
├── main.py
├── config.py
├── question_generator.py
├── leaderboard.py
├── voice.py
├── tts.py
├── countdown_ring.py
├── celebrate.py
├── buildozer.spec
├── requirements.txt
├── README.md
└── vosk-model-small-zh-cn-0.22/
    ├── am/
    ├── conf/
    ├── graph/
    └── ...
```

---

## 三、桌面调试（强烈建议先做）

在打包前，先在电脑上跑通整个流程：

```bash
cd /path/to/kids_math_kivy
source venv/bin/activate
python main.py
```

你应该看到：
1. 出现一个蓝色背景的窗口，标题"数学小天才"
2. 三个大按钮：简单 / 普通 / 困难
3. 点击任一按钮 → 听到 TTS 说"准备好了请说开始"
4. 屏幕显示题目，倒计时圆环开始转动
5. 用数字键盘输入答案 → 提交 → 答对撒花、答错提示

**调试清单**：
- [ ] 界面正常显示，无报错
- [ ] 三种难度都能出题
- [ ] 倒计时正常递减
- [ ] 答对/答错逻辑正确
- [ ] 排行榜能保存和显示
- [ ] 语音识别可用（终端能看到 `[Voice] 识别: xxx` 日志）

> 如果语音识别报模型路径错误，检查 `voice.py` 中 `MODEL_DIR` 路径是否正确。

---

## 四、Buildozer 打包 APK

### 4.1 初始化（如果 buildozer.spec 已存在可跳过）

```bash
cd /path/to/kids_math_kivy
buildozer init
```

项目已自带 `buildozer.spec`，无需再生成。直接编辑它即可。

### 4.2 关键配置说明

打开 `buildozer.spec`，确认以下关键项：

```ini
[app]
title = KidsMath
package.name = kidsmath
package.domain = com.kidsmath          # 改为你自己的域名倒写

requirements = python3==3.11.9, kivy==2.3.1, vosk==0.3.45, pyaudio==0.2.13, numpy, pillow

android.permissions = RECORD_AUDIO, CAMERA, INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a              # 华为平板几乎都是这个架构

orientation = landscape                 # 横屏
fullscreen = 1
```

### 4.3 开始打包

```bash
# 首次构建（耗时 20-60 分钟，会下载 SDK/NDK）
buildozer -v android debug
```

构建过程会：
1. 自动下载 Android SDK、NDK、Gradle
2. 创建 Python-for-Android 的 Python 环境
3. 编译所有依赖（包括 Vosk 的 C++ 部分，最慢）
4. 打包成 APK

成功后输出：
```
# Buildozer will print:
APK filename: /path/to/kids_math_kivy/bin/KidsMath-0.1-arm64-v8a-debug.apk
```

### 4.4 常见构建错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `Could not find a version that satisfies the requirement vosk` | Vosk 无 arm64 轮子 | 升级 pip + 使用 Vosk 0.3.45+ |
| `Permission denied` for SDK | 权限问题 | `sudo chown -R $USER ~/.buildozer` |
| NDK 下载失败 | 网络问题 | 手动下载 NDK r25b 并配置 `android.ndk_path` |
| 内存不足 | Buildozer 编译耗内存 | 给 WSL2 分配更多内存（编辑 `.wslconfig`） |
| `pyaudio` 编译失败 | 缺少 portaudio | `sudo apt install portaudio19-dev` |

### 4.5 配置 WSL2 内存（如需要）

在 Windows 用户目录下创建 `.wslconfig`：
```
[wsl2]
memory=8GB
processors=4
swap=4GB
```

---

## 五、安装到华为平板

### 5.1 开启开发者模式

1. 设置 → 关于平板 → 连续点击"版本号" 7 次
2. 返回 → 系统和更新 → 开发者选项
3. 开启 **USB 调试**
4. 华为特有：关闭 **"纯净模式"**（设置 → 安全 → 纯净模式）

### 5.2 安装方式 A：USB 直接部署（推荐调试用）

```bash
# 平板通过 USB 连接电脑，确认 adb 能识别
adb devices

# 一键部署 + 运行 + 看日志
buildozer -v android debug deploy run logcat
```

### 5.3 安装方式 B：手动拷贝 APK

```bash
# 拷贝到平板
adb push bin/KidsMath-0.1-arm64-v8a-debug.apk /sdcard/Download/

# 在平板上：文件管理 → Download → 点击 APK → 安装
```

### 5.4 安装方式 C：局域网传输

- 把 APK 传到微信文件助手 / QQ / 网盘
- 在平板上直接下载安装

---

## 六、发布版本（上架应用市场）

### 6.1 生成签名密钥

```bash
keytool -genkey -v -keystore kidsmath-release.keystore \
    -alias kidsmath -keyalg RSA -keysize 2048 -validity 10000
```

### 6.2 配置签名

在 `buildozer.spec` 末尾添加：

```ini
# 发布签名
android.release_artifact = apk
# 在 [app] 段添加：
# android.signing.release = True
# android.signing.release_keystore = /path/to/kidsmath-release.keystore
# android.signing.release_keyalias = kidsmath
# android.signing.release_keystore_password = your_password
# android.signing.release_key_password = your_password
```

### 6.3 构建发布版

```bash
buildozer -v android release
# 输出: bin/KidsMath-0.1-arm64-v8a-release.apk
```

### 6.4 上架华为应用市场

1. 注册 [华为开发者联盟](https://developer.huawei.com/consumer/cn/) 账号
2. 实名认证（个人/企业）
3. 创建应用 → 上传 APK → 填写资料 → 提交审核
4. 审核周期通常 1-3 个工作日

> ⚠️ 华为应用市场要求 **targetSdkVersion ≥ 30**，确保 `android.api = 33` 或更高。

---

## 七、项目结构

```
kids_math_kivy/
├── main.py                  # 主程序：界面 + 游戏流程
├── config.py                # 全局配置（难度、颜色、路径）
├── question_generator.py    # 出题器
├── leaderboard.py           # 排行榜（JSON 存储）
├── voice.py                 # 语音识别（Vosk 离线中文）
├── tts.py                   # 语音播报（TTS）
├── countdown_ring.py        # 倒计时圆环 Widget
├── celebrate.py             # 撒花庆祝动画
├── buildozer.spec           # Buildozer 打包配置
├── requirements.txt         # Python 依赖
├── README.md                # 本文档
├── data/                    # 运行时自动创建
│   ├── leaderboard.json     # 排行榜数据
│   └── avatars/             # 头像照片
└── vosk-model-small-zh-cn-0.22/  # 语音模型（需手动下载）
```

---

## 八、核心参数调优

在 `config.py` 中调整游戏体验：

```python
DIFFICULTY_CONFIG = {
    "easy": {
        "base_time": 20,        # 首题倒计时（秒）—— 越大越宽松
        "min_time": 8,          # 最低底线 —— 保护小朋友不焦虑
        "time_decay": 0.3,      # 每题递减量 —— 越大越紧张
        "max_wrong": 5,         # 允许错误次数 —— 越大越宽容
        "total_questions": 15,   # 总题数
        "score_per_question": 10,
    },
    # ... normal / hard 同理
}
```

**调参建议**：
- 3-4 岁初次接触：把 `base_time` 调到 30，`min_time` 调到 15
- 想增加挑战：`time_decay` 加大，`max_wrong` 减小
- 课堂使用：`total_questions` 设为 10，一节课内可完成

---

## 九、语音识别说明

### 9.1 支持的说法

| 场景 | 识别关键词 | 示例 |
|------|-----------|------|
| 开始游戏 | "开始" | "好了开始"、"准备开始" |
| 回答数字 | 阿拉伯数字 / 中文数字 | "5"、"十五"、"二十三"、"一百" |

### 9.2 识别原理

- **引擎**：Vosk（CMU Sphinx 后继者，Kaldi 系）
- **模型**：`vosk-model-small-zh-cn-0.22`（40MB，离线）
- **采样率**：16kHz 单声道
- **延迟**：约 0.3-0.5 秒

### 9.3 无麦克风/识别失败时的备选

- 点击屏幕任意位置即可跳过"等待开始"
- 数字键盘全程可用，触屏点击即可作答

---

## 十、故障排查

### 10.1 应用启动闪退

```bash
# 查看日志
adb logcat | grep python
adb logcat | grep kidsmath
```

常见原因：
- 模型目录路径错误 → 检查 `voice.py` 中 `MODEL_DIR`
- 权限被拒 → 在系统设置中手动授予麦克风/相机权限
- 内存不足 → 关闭其他应用

### 10.2 语音识别不工作

- 确认平板已授予 **麦克风权限**
- 检查模型文件是否完整解压
- 终端/日志中查看 `[Voice]` 开头的提示

### 10.3 拍照黑屏

- 确认已授予 **相机权限**
- 部分平板前置/后置摄像头索引不同，可在 `CameraPopup` 中尝试 `index=1`

### 10.4 倒计时太快/太慢

- 修改 `config.py` 中的 `base_time` 和 `time_decay`
- 重新打包安装

---

## 十一、开发工作流建议

```
写代码 → 桌面 python main.py 调试
    ↓ 确认无报错
buildozer android debug → 装到平板测试
    ↓ 确认功能正常
调优参数 → 再打包 → 再测试
    ↓ 满意后
buildozer android release → 上架应用市场
```

---

## 十二、许可与致谢

- Kivy: https://kivy.org （MIT 许可）
- Vosk: https://alphacephei.com/vosk （Apache 2.0）
- Buildozer: https://buildozer.readthedocs.io （MIT 许可）

---

**祝小朋友玩得开心，数学越来越棒！** 🎉
