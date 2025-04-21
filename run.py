import sys
import os
import argparse
import importlib.util
import subprocess

# 定义需要检查和安装的依赖项 (包名, 检查的模块名)
REQUIRED_PACKAGES = [
    ("PyQt6", "PyQt6"),
    ("requests", "requests"),
    ("torch", "torch"),
    ("torchvision", "torchvision"),
    ("Pillow", "PIL"),
    ("numpy", "numpy"),
]

def check_and_install_dependencies():
    """检查并安装缺失的Python依赖项"""
    print("开始检查项目依赖...")
    missing_packages = []
    for package_name, module_name in REQUIRED_PACKAGES:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            print(f"  -> 未找到依赖包: {package_name} (模块: {module_name})")
            missing_packages.append(package_name)
        else:
            print(f"  -> 依赖包已找到: {package_name}")

    if not missing_packages:
        print("所有核心依赖项均已安装。")
        return True

    print("\n尝试安装缺失的依赖项...")
    try:
        # 使用 check_call 会在失败时抛出异常
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("缺失的依赖项已成功安装。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n错误：安装依赖项失败。请尝试手动运行: pip install {' '.join(missing_packages)}")
        print(f"错误详情: {e}")
        return False
    except FileNotFoundError:
        print("\n错误：找不到 'pip' 命令。请确保 pip 已安装并位于您的系统 PATH 中。")
        return False

if __name__ == "__main__":
    # 1. 首先检查并安装依赖
    if not check_and_install_dependencies():
        print("依赖安装失败，无法继续运行。")
        sys.exit(1) # 依赖失败则退出
    
    # 2. 依赖检查通过后，再导入可能依赖这些库的模块
    try:
        from gui.main import main
    except ImportError as e:
        print(f"错误：导入 GUI 模块失败: {e}")
        print("即使依赖检查通过，导入仍然失败。请检查您的 Python 环境和项目结构。")
        sys.exit(1)

    # 3. 解析命令行参数
    parser = argparse.ArgumentParser(description="Minecraft AI")
    parser.add_argument("--local", action="store_true", help="使用本地模型")
    parser.add_argument("--cache", action="store_true", help="启用缓存")
    parser.add_argument("--prediction", action="store_true", help="启用动作预测")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--vision", action="store_true", help="启用视觉学习系统")
    args = parser.parse_args()
    
    # 4. 设置环境变量
    if args.local:
        os.environ["USE_LOCAL_MODEL"] = "1"
    if args.cache:
        os.environ["USE_CACHE"] = "1"
    if args.prediction:
        os.environ["USE_PREDICTION"] = "1"
    if args.debug:
        os.environ["DEBUG"] = "1"
    # 默认启用视觉系统，除非显式禁用 (添加 --no-vision 参数?)
    # For now, always set based on original logic
    os.environ["USE_VISION"] = "1"
    
    # 5. 启动应用
    try:
        main()
    except Exception as e:
        print("\n--- 应用程序运行时发生未捕获的错误 ---")
        import traceback
        traceback.print_exc()
        print("--------------------------------------")
        # Optional: Keep console open on error in Windows
        if sys.platform == "win32":
            input("按 Enter 键退出...")
        sys.exit(1) 