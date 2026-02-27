[app]

# 应用名称
title = 跳一跳助手

# 包名
package.name = jumpjumpauto
package.domain = com.jumpjump.auto

# 源码目录
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# 版本
version = 1.0

# 依赖
requirements = python3,kivy,pillow

# 方向
orientation = portrait

[buildozer]

# 日志级别
log_level = 2

[android]

# 权限
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# 架构
android.archs = armeabi-v7a,arm64-v8a

# 最小 SDK
android.minapi = 21

[android.meta]

# 在 Google Play 发布（可选）
#android.add_manifest =
#android.manifest_placeholders = [:]

[android.ndk]

[android.sdk]
