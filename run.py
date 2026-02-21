"""
Minecraft AI 启动脚本
检查依赖 → 启动 GUI
"""

import sys
import os
import argparse
import importlib.util
import subprocess

REQUIRED_PACKAGES = [
    ("PyQt6", "PyQt6"),
    ("requests", "requests"),
]


def check_and_install_dependencies():
    print("检查项目依赖...")
    missing = []
    for pkg_name, mod_name in REQUIRED_PACKAGES:
        if importlib.util.find_spec(mod_name) is None:
            print(f"  -> 未找到: {pkg_name}")
            missing.append(pkg_name)
        else:
            print(f"  -> 已安装: {pkg_name}")

    if not missing:
        print("所有依赖已就绪。")
        return True

    print(f"\n正在安装: {', '.join(missing)}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + missing
        )
        print("安装完成。")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"安装失败: {e}")
        print(f"请手动运行: pip install {' '.join(missing)}")
        return False


if __name__ == "__main__":
    if not check_and_install_dependencies():
        sys.exit(1)

    try:
        from gui.main import main
    except ImportError as e:
        print(f"导入 GUI 失败: {e}")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Minecraft AI")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()

    if args.debug:
        os.environ["DEBUG"] = "1"

    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        if sys.platform == "win32":
            input("按 Enter 退出...")
        sys.exit(1)
