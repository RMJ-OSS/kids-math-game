[app]

# 应用标题（中文在 Android 上会被转义，打包后可在手机设置里改）
title = KidsMath
package.name = kidsmath
package.domain = com.kidsmath
version = 1.0
# 源码目录
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,wav,mp3
source.exclude_exts = spec,md
source.exclude_dirs = tests, __pycache__, .git

# 入口
main.filename = main.py

# 依赖（关键）
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.1,vosk==0.3.45,numpy,pillow

# 权限（华为/安卓通用）
android.permissions = RECORD_AUDIO, CAMERA, INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.features = android.hardware.microphone, android.hardware.camera

# Android 版本
android.api = 33
android.minapi = 24
android.sdk = 33
android.ndk = 25b
android.ndk_path =
android.sdk_path =
android.accept_sdk_license = True
# 架构（华为平板多为 arm64-v8a）
android.archs = arm64-v8a

# 横屏（平板体验更好）
orientation = landscape

# 全屏
fullscreen = 1

# 图标（需自行放入 icons/ 目录）
# icon.filename = icons/icon.png
# presplash.filename = icons/presplash.png

[buildozer]

# 日志级别
log_level = 2
warn_on_root = 1

# Android 构建
android.build_type = debug  # 发布时改为 release

# 清理
android.clean_build = 0
