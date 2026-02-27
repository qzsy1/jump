# 在线打包 APK 操作指南

## 方法一：GitHub Actions 自动打包（推荐）

### 步骤 1：创建 GitHub 仓库

1. 访问 https://github.com/new
2. 创建新仓库，名称如 `jump-jump-auto`
3. **不要**勾选 "Initialize this repository with a README"
4. 点击 "Create repository"

### 步骤 2：推送代码到 GitHub

在你的电脑上打开 **Git Bash** 或 **PowerShell**，运行：

```bash
cd C:\Users\xlq\jump_jump_auto

# 初始化 Git（如果还没有）
git init
git add .
git commit -m "Initial commit"

# 添加远程仓库（替换为你的用户名和仓库名）
git remote add origin https://github.com/你的用户名/jump-jump-auto.git

# 推送代码
git branch -M main
git push -u origin main
```

### 步骤 3：触发构建

推送代码后，GitHub 会自动开始构建：

1. 访问你的仓库：https://github.com/你的用户名/jump-jump-auto
2. 点击 **Actions** 标签
3. 等待构建完成（约 10-20 分钟）
4. 构建完成后，点击进入该次构建
5. 在底部的 **Artifacts** 区域下载 `jump-jump-apk`

### 手动触发构建

如果不想推送代码，可以手动触发：

1. 访问仓库
2. 点击 **Actions** → **Build Android APK**
3. 点击 **Run workflow**
4. 选择分支（main），点击绿色按钮

---

## 方法二：Replit 在线打包

### 步骤 1：创建 Replit 项目

1. 访问 https://replit.com
2. 点击 "+ Create Repl"
3. 选择 Python 模板
4. 命名为 `jump-jump-auto`

### 步骤 2：上传代码

1. 在 Replit 左侧文件面板
2. 点击 "+ New File"
3. 将以下文件内容复制粘贴：
   - `main.py` (从 `C:\Users\xlq\jump_jump_auto\android\main.py`)
   - `jump.kv` (从 `C:\Users\xlq\jump_jump_auto\android\jump.kv`)

### 步骤 3：运行打包命令

在 Replit 的 Shell 中运行：

```bash
# 安装依赖
pip install kivy python-for-android

# 构建 APK
python -m pythonforandroid.toolchain apk \
  --private \
  --name="跳一跳助手" \
  --version=1.0 \
  --package=com.jumpjump.auto \
  --bootstrap=sdl2 \
  --requirements=kivy,opencv-python-headless,pillow,pyjnius \
  --arch=armeabi-v7a \
  --orientations=portrait \
  main.py
```

### 步骤 4：下载 APK

构建完成后，APK 文件在 `bin/` 目录，可以下载。

---

## 方法三：Buildozer.io（官方打包工具）

1. 访问 https://buildozer.io/
2. 按照网站指引操作
3. 需要配置 `buildozer.spec` 文件

---

## 下载 APK 后安装到手机

连接手机到电脑，运行：

```bash
adb install 跳一跳助手-1.0-armeabi-v7a-debug.apk
```

或在手机上直接打开 APK 文件安装。

---

## 常见问题

**Q: GitHub Actions 构建失败**
A:
1. 检查 `android/main.py` 文件是否存在
2. 查看 Actions 日志中的错误信息
3. 确保代码已正确推送到 GitHub

**Q: Replit 构建超时**
A:
1. Replit 免费版有时间限制
2. 建议使用 GitHub Actions（免费且稳定）

**Q: APK 安装失败**
A:
1. 确保手机开启"允许安装未知来源"
2. Android 版本需要 5.0 或更高
