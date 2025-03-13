import sys
import os
import argparse
from gui.main import main

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="MinecraftAI")
    parser.add_argument("--local", action="store_true", help="使用本地模型")
    parser.add_argument("--cache", action="store_true", help="启用缓存")
    parser.add_argument("--prediction", action="store_true", help="启用动作预测")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    args = parser.parse_args()
    
    # 设置环境变量
    if args.local:
        os.environ["USE_LOCAL_MODEL"] = "1"
    if args.cache:
        os.environ["USE_CACHE"] = "1"
    if args.prediction:
        os.environ["USE_PREDICTION"] = "1"
    if args.debug:
        os.environ["DEBUG"] = "1"
        
    # 启动应用
    main() 