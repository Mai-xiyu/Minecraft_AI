import logging
import torch
import torchvision.models as models
from torchvision import transforms
from PIL import Image
import os

# 设置日志记录
logger = logging.getLogger("MinecraftAI.Vision")
logger.setLevel(logging.INFO)

class VisionLearningSystem:
    """
    处理 Minecraft 视觉信息，进行学习和分析。
    """
    def __init__(self, model_name='MobileNet', device=None):
        """
        初始化视觉学习系统。

        Args:
            model_name (str): 要使用的预训练模型名称 ('ResNet', 'MobileNet', etc.)。
            device (str, optional): 指定运行模型的设备 ('cuda', 'cpu', None for auto-detect)。
        """
        self.logger = logging.getLogger("MinecraftAI.VisionLearning")
        self.logger.info(f"Initializing Vision Learning System with model: {model_name}")

        self.device = device
        if self.device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.logger.info(f"Using device: {self.device}")

        self.model = self._load_model(model_name)
        self.model.to(self.device)
        self.model.eval() # 默认设置为评估模式

        # 定义图像预处理转换
        # 注意：_load_model 可能会根据模型覆盖这个预处理
        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self.logger.info("Vision Learning System initialized.")

    def _load_model(self, model_name):
        """加载指定的预训练模型"""
        self.logger.info(f"Loading pre-trained model: {model_name}")
        # 缓存目录
        model_dir = os.path.join(os.path.expanduser("~"), ".minecraft_ai", "models")
        os.makedirs(model_dir, exist_ok=True)
        torch.hub.set_dir(model_dir)

        try:
            if model_name.lower() == 'mobilenet':
                # weights=models.MobileNet_V2_Weights.DEFAULT 适用于较新 torchvision
                if hasattr(models, 'MobileNet_V2_Weights'):
                     weights = models.MobileNet_V2_Weights.DEFAULT
                     self.preprocess = weights.transforms() # 使用模型推荐的预处理
                     model = models.mobilenet_v2(weights=weights)
                else: # 兼容旧版本
                    self.logger.warning("Using legacy pretrained=True for MobileNetV2. Consider upgrading torchvision.")
                    model = models.mobilenet_v2(pretrained=True)
                    # Keep default preprocess if using legacy
                # 替换分类器以适应特定任务（如果需要）
                # num_ftrs = model.classifier[1].in_features
                # model.classifier[1] = torch.nn.Linear(num_ftrs, num_classes) # Replace num_classes
            elif model_name.lower() == 'resnet':
                if hasattr(models, 'ResNet18_Weights'):
                    weights = models.ResNet18_Weights.DEFAULT
                    self.preprocess = weights.transforms()
                    model = models.resnet18(weights=weights)
                else:
                     self.logger.warning("Using legacy pretrained=True for ResNet18. Consider upgrading torchvision.")
                     model = models.resnet18(pretrained=True)
                     # Keep default preprocess if using legacy
                # num_ftrs = model.fc.in_features
                # model.fc = torch.nn.Linear(num_ftrs, num_classes)
            else:
                self.logger.warning(f"Unsupported model name: {model_name}. Falling back to MobileNetV2.")
                model_name = 'MobileNet' # Update model_name for logging consistency
                if hasattr(models, 'MobileNet_V2_Weights'):
                     weights = models.MobileNet_V2_Weights.DEFAULT
                     self.preprocess = weights.transforms()
                     model = models.mobilenet_v2(weights=weights)
                else:
                    self.logger.warning("Using legacy pretrained=True for MobileNetV2 fallback. Consider upgrading torchvision.")
                    model = models.mobilenet_v2(pretrained=True)

            self.logger.info(f"Model {model_name} loaded successfully.")
            return model
        except Exception as e:
            self.logger.error(f"Error loading model {model_name}: {e}")
            raise # 重新抛出异常，让调用者知道加载失败

    def process_frame(self, image: Image.Image):
        """
        对单个图像帧进行预处理并提取特征。

        Args:
            image (PIL.Image.Image): 输入的图像帧。

        Returns:
            torch.Tensor: 从模型中提取的特征张量。
                         或者在评估模式下返回模型的原始输出。
        """
        if self.model is None:
            self.logger.error("Model is not loaded.")
            return None
        try:
            # 确保图像是 RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            input_tensor = self.preprocess(image)
            input_batch = input_tensor.unsqueeze(0) # 创建一个 mini-batch 作为模型输入
            input_batch = input_batch.to(self.device)

            with torch.no_grad():
                output = self.model(input_batch)

            # 根据需要处理输出：
            # 1. 如果是分类任务，可能需要对 output 应用 softmax 并获取预测类别
            # probabilities = torch.nn.functional.softmax(output[0], dim=0)
            # top_prob, top_catid = torch.topk(probabilities, 1)
            # return top_catid.item()

            # 2. 如果是提取特征，可能需要获取模型中间层的输出或最终的特征向量
            # return output # 返回模型的原始输出或处理后的特征

            # 暂时只返回原始输出
            return output

        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            import traceback
            traceback.print_exc() # Print stack trace for debugging
            return None

    def learn_from_frame(self, image: Image.Image, context_data: dict, action: dict, result: dict):
        """
        （占位符）根据图像帧、上下文、执行的动作和结果进行学习。
        这部分通常需要更复杂的逻辑，例如强化学习或监督学习更新。

        Args:
            image (PIL.Image.Image): 视觉输入。
            context_data (dict): 执行动作时的状态信息。
            action (dict): AI 决定执行的动作。
            result (dict): 执行动作后的结果。
        """
        self.logger.debug("Learn from frame called (Placeholder).")
        # 在这里实现学习逻辑，例如：
        # 1. 提取图像特征
        # features = self.process_frame(image)
        # 2. 将特征与上下文、动作、结果关联起来
        # 3. 更新模型参数（如果模型需要训练）
        # 4. 或者存储经验用于离线学习
        pass

    def get_visual_context_description(self, image: Image.Image) -> str:
        """
        （占位符）处理图像并返回一个文本描述，用于注入到 LLM 提示中。

        Args:
            image (PIL.Image.Image): 输入的图像帧。

        Returns:
            str: 对图像内容的文本描述。
        """
        self.logger.debug("Get visual context description called (Placeholder).")
        # 这里可以使用图像字幕模型，或者简单的对象检测结果
        # features = self.process_frame(image)
        # description = self._generate_description_from_features(features)
        # return description
        return "Visual context is present." # 简单的占位符描述

# 可以添加一些辅助函数，例如下载模型文件等

if __name__ == '__main__':
    # 配置基本的日志记录器以查看测试输出
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # 用于测试该模块的基本功能
    print("Testing VisionLearningSystem...")
    try:
        # 创建一个假的黑色图像进行测试
        img = Image.new('RGB', (600, 400), color = 'black')

        # 测试 MobileNet
        print("\nTesting MobileNetV2...")
        vision_system_mobilenet = VisionLearningSystem(model_name='MobileNet')
        output_mobilenet = vision_system_mobilenet.process_frame(img)
        if output_mobilenet is not None:
            print(f"MobileNet output shape: {output_mobilenet.shape}")
        vision_system_mobilenet.learn_from_frame(img, {}, {}, {})
        desc_mobilenet = vision_system_mobilenet.get_visual_context_description(img)
        print(f"MobileNet context description: {desc_mobilenet}")

        # 测试 ResNet (如果需要)
        # print("\nTesting ResNet18...")
        # vision_system_resnet = VisionLearningSystem(model_name='ResNet')
        # output_resnet = vision_system_resnet.process_frame(img)
        # if output_resnet is not None:
        #     print(f"ResNet output shape: {output_resnet.shape}")

        print("\nVisionLearningSystem test completed.")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc() 