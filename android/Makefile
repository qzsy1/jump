.PHONY: all clean install deps run test apk push

all: deps run

deps:
	@echo "安装依赖..."
	pip install -r requirements.txt

run:
	@echo "桌面测试模式..."
	python desktop_test.py

apk:
	@echo "开始打包 APK..."
	python -m pythonforandroid.toolchain apk --private \
		--name="跳一跳助手" \
		--version=1.0 \
		--package=com.jumpjump.auto \
		--bootstrap=sdl2 \
		--requirements=kivy,opencv-python-headless,pillow,pyjnius \
		--arch=armeabi-v7a \
		--orientations=portrait \
		main.py

install:
	@echo "安装到手机..."
	@echo "请连接手机并授权 ADB"
	python -m pythonforandroid.toolchain adb install \
		--package=com.jumpjump.auto \
		--name="跳一跳助手"

push: apk install
	@echo "打包并安装完成！"

clean:
	@echo "清理缓存..."
	rm -rf bin/ build/ dist/

test:
	@echo "运行测试..."
	python -c "from main import JumpAlgorithm, JumpConfig; print('Core algorithm OK')"

help:
	@echo "可用命令:"
	@echo "  make deps     - 安装依赖"
	@echo "  make run      - 桌面测试"
	@	@echo "  make apk      - 打包 APK"
	@echo "  make install  - 安装到手机"
	@echo "  make push     - 打包并安装"
	@echo "  make clean    - 清理缓存"
	@echo "  make test     - 测试算法"
	@echo "  make help     - 显示帮助"
