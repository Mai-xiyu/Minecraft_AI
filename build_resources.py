import os
from pathlib import Path
from PIL import Image
import shutil

def create_resources():
    """创建资源目录和图标"""
    # 创建资源目录
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    # 创建图标
    icon_size = (256, 256)
    icon = Image.new('RGBA', icon_size, (0, 0, 0, 0))
    
    # 绘制简单的图标
    # 这里只是一个示例，你可以替换成你自己的图标设计
    from PIL import ImageDraw
    draw = ImageDraw.Draw(icon)
    
    # 绘制一个简单的立方体
    cube_color = (65, 173, 73)  # Minecraft绿色
    points = [
        (128, 50),   # 顶部中心
        (78, 100),   # 左上
        (178, 100),  # 右上
        (128, 150),  # 底部中心
        (78, 200),   # 左下
        (178, 200),  # 右下
    ]
    
    # 绘制立方体边
    draw.line([points[0], points[1]], fill=cube_color, width=3)
    draw.line([points[0], points[2]], fill=cube_color, width=3)
    draw.line([points[1], points[3]], fill=cube_color, width=3)
    draw.line([points[2], points[3]], fill=cube_color, width=3)
    draw.line([points[1], points[4]], fill=cube_color, width=3)
    draw.line([points[2], points[5]], fill=cube_color, width=3)
    draw.line([points[3], points[4]], fill=cube_color, width=3)
    draw.line([points[3], points[5]], fill=cube_color, width=3)
    
    # 保存为ICO文件
    icon.save(resources_dir / "icon.ico", format="ICO")
    
    # 处理二维码图片
    qr_files = {
        'alipay.jpg': 'alipay.png',
        'wechat.jpg': 'wechat.png'
    }
    
    for src_name, dst_name in qr_files.items():
        src_path = Path(src_name)
        if src_path.exists():
            # 打开并转换图片
            img = Image.open(src_path)
            # 调整大小为400x400，保持比例
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
            # 保存为PNG
            img.save(resources_dir / dst_name, 'PNG')
            print(f"已转换并保存: {dst_name}")
    
    print("资源文件创建完成")

if __name__ == "__main__":
    create_resources() 