import argparse
import logging
import json
import time
import requests
from .agent import MinecraftAgent
from .deepseek_api import DeepSeekAPI

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("MinecraftAI")

def main():
    """AI主程序"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Minecraft AI")
    parser.add_argument("--api_key", required=True, help="DeepSeek API密钥")
    parser.add_argument("--steps", type=int, default=100, help="执行步数")
    parser.add_argument("--delay", type=float, default=2, help="每步延迟(秒)")
    parser.add_argument("--task", default="gather_wood", help="初始任务")
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    logger.info("启动Minecraft AI")
    
    try:
        # 创建API客户端
        api = DeepSeekAPI(args.api_key)
        
        # 创建AI代理
        agent = MinecraftAgent(api)
        
        # 设置初始任务
        agent.set_task(args.task)
        
        # 主循环
        for step in range(args.steps):
            logger.info(f"Step {step + 1}/{args.steps}")
            
            # 执行一步
            success = agent.step()
            if not success:
                logger.error("执行失败，停止运行")
                break
            
            # 延迟
            time.sleep(args.delay)
        
        logger.info("AI运行完成")
        
    except Exception as e:
        logger.error(f"AI运行出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 