[app]

title = 跳一跳助手
package.name = jumpjumpauto
package.domain = com.jumpjump.auto

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
source.exclude_dirs = tests, bin, .git, __pycache__, build

version = 1.0

requirements = kivy,pillow

icon.filename = assets/icon.png

orientation = portrait

[buildozer]

log_level = 2

[android]

android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.archs = armeabi-v7a,arm64-v8a

[android.ndk]

[android.sdk]
