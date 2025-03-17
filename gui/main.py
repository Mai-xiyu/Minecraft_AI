import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from .main_window import MainWindow

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

def main():
    # 确保存在环境变量
    if "DEEPSEEK_API_KEY" in os.environ:
        api_key = os.environ["DEEPSEEK_API_KEY"]
        logging.info("已从环境变量读取API密钥")
    
    # 创建应用程序
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # 执行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 