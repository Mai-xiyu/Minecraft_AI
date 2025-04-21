import logging
from PIL import Image
import requests
import base64
from io import BytesIO

# 设置日志记录
logger = logging.getLogger("MinecraftAI.VisionCapture")
logger.setLevel(logging.INFO)

class MinecraftVisionCapture:
    """
    负责从 Minecraft Bot 服务器捕获视觉帧。
    """
    def __init__(self, bot_server_url="http://localhost:3002"):
        """
        初始化视觉捕获系统。

        Args:
            bot_server_url (str): Bot服务器的地址。
        """
        self.logger = logging.getLogger("MinecraftAI.VisionCapture")
        self.bot_server_url = bot_server_url
        self.vision_endpoint = f"{self.bot_server_url}/bot/vision"
        self.logger.info(f"Vision Capture initialized. Endpoint: {self.vision_endpoint}")

    def get_latest_frame(self) -> Image.Image | None:
        """
        从 Bot 服务器获取最新的视觉帧。

        Returns:
            PIL.Image.Image | None: 最新的图像帧，如果获取失败则返回 None。
        """
        try:
            response = requests.get(self.vision_endpoint, timeout=5) # 设置超时
            response.raise_for_status() # 检查 HTTP 错误

            data = response.json()
            if data.get("success") and data.get("data"):
                # 假设返回的是 data:image/png;base64,... 格式
                base64_data = data["data"].split('base64,')[-1]
                image_data = base64.b64decode(base64_data)
                image = Image.open(BytesIO(image_data))
                # self.logger.debug("Successfully retrieved and decoded frame.")
                return image
            elif data.get("error"):
                self.logger.warning(f"Failed to get frame from bot server: {data['error']}")
                return None
            else:
                self.logger.warning("Received success=false or no data from vision endpoint.")
                return None

        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout connecting to vision endpoint: {self.vision_endpoint}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error requesting frame from {self.vision_endpoint}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing frame data: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == '__main__':
    # 配置基本的日志记录器以查看测试输出
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print("Testing MinecraftVisionCapture...")
    # 注意：这个测试需要 Bot 服务器正在运行并提供 /bot/vision 端点
    capture = MinecraftVisionCapture()
    frame = capture.get_latest_frame()
    if frame:
        print(f"Successfully captured frame. Size: {frame.size}, Mode: {frame.mode}")
        # 可以选择性地显示或保存图像
        # frame.show()
        # frame.save("test_capture.png")
    else:
        print("Failed to capture frame. Is the bot server running and configured?")
    print("Test finished.") 