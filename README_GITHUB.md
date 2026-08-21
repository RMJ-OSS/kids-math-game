# 数学小天才 —— 三步拿到 APK

> 全程只需浏览器操作，不用装任何软件。预计 20-30 分钟拿到安装包。

---

## 第 1 步：建仓库

1. 打开 https://github.com/signup 注册（已有账号跳过）
2. 登录后点右上角 **+ → New repository**
3. 仓库名填 `kids-math-game`
4. ⚠️ **不要**勾选任何复选框（README/.gitignore/license 都别勾）
5. 选 **Public**
6. 点 **Create repository**

## 第 2 步：上传文件

1. 进入刚建好的空仓库
2. 点 **"uploading an existing file"**
3. 打开你电脑里的 `kids_math_kivy` 文件夹
4. 把里面**所有文件**拖进网页（包含隐藏的 `.github` 文件夹，必须一起传！）
5. 点 **Commit changes**

## 第 3 步：触发打包并下载

1. 仓库页面点 **Actions** 选项卡
2. 左侧点 **Build Kids Math APK**
3. 右侧点绿色 **Run workflow → Run workflow**
4. 等 15-30 分钟，看到 ✅ 绿色勾
5. 滚到下方 **Artifacts** → 点 `kids-math-game-apk` 下载
6. 解压得到 `.apk`，传到华为平板安装即可

---

## 装到平板上

1. 把 APK 通过微信/数据线传到平板
2. 平板打开文件管理器，点击 APK
3. 若提示"风险应用"：设置 → 安全 → 安装未知来源应用 → 给文件管理器授权
4. 安装完成，打开即可

---

## 出问题怎么办

| 现象 | 解决办法 |
|------|----------|
| Actions 里看不到工作流 | `.github` 文件夹没传上去，重新上传 |
| 构建红字失败 | 点进运行记录看日志，截图发给我 |
| 安装提示"解析失败" | 确保下载的是 APK 不是 ZIP，重新解压 |
| 平板是纯血鸿蒙装不了 | 此方案仅支持 HarmonyOS 4 及以下 |

---

## 文件清单（确认都上传了）

```
.github/workflows/build_apk.yml   ← 自动打包脚本（必须有）
main.py
config.py
question_generator.py
leaderboard.py
voice.py
tts.py
countdown_ring.py
celebrate.py
buildozer.spec
requirements.txt
.gitignore
README.md
```
