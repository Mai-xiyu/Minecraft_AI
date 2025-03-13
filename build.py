import os
import shutil
import subprocess
from pathlib import Path
import json
import sys

def create_spec():
    """创建PyInstaller规范文件"""
    return """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 收集所有Python文件和资源
a = Analysis(
    ['gui/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ai', 'ai'),
        ('bot', 'bot'),          # 确保bot目录被包含
        ('config.json', '.'),
        ('resources', 'resources'),
        ('memory.json', '.'),    # 如果存在
    ],
    hiddenimports=[
        'ai.agent',
        'ai.deepseek_api',
        'ai.memory',
        'ai.learning',
        'ai.prompts',
        'test_connection',
        'PyQt6',
        'requests'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 创建可执行文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MinecraftAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico'
)
"""

def check_nodejs_env():
    """检查 Node.js 环境"""
    try:
        # 获取 npm 路径
        npm_paths = [
            r"C:\Program Files\nodejs\npm.cmd",
            r"C:\Program Files (x86)\nodejs\npm.cmd",
            os.path.join(os.environ.get('APPDATA', ''), 'npm', 'npm.cmd'),
            "npm.cmd",  # 在 PATH 中查找
            "npm"       # Linux/Mac
        ]
        
        npm_path = None
        for path in npm_paths:
            if os.path.exists(path):
                npm_path = path
                break
        
        if not npm_path:
            print("错误: 未找到 npm，请确保 Node.js 正确安装")
            print("1. 下载 Node.js: https://nodejs.org/")
            print("2. 安装时勾选 'Add to PATH'")
            print("3. 重启电脑")
            return False
            
        # 测试 npm 是否可用
        result = subprocess.run(
            [npm_path, "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"npm 版本: {result.stdout.strip()}")
            return True
        else:
            print(f"npm 测试失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"检查 Node.js 环境时出错: {e}")
        return False

def get_npm_path():
    """获取 npm 路径"""
    try:
        # 获取 npm 版本信息来确定 npm 路径
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # 如果能运行 npm --version，说明 npm 在 PATH 中
            if os.name == 'nt':  # Windows
                return 'npm.cmd'
            return 'npm'
            
        return None
    except Exception:
        # 尝试常见的 npm 安装路径
        npm_paths = [
            r"C:\Program Files\nodejs\npm.cmd",
            r"C:\Program Files (x86)\nodejs\npm.cmd",
            os.path.join(os.environ.get('APPDATA', ''), 'npm', 'npm.cmd'),
            "npm.cmd",  # Windows
            "npm"       # Unix-like
        ]
        
        for path in npm_paths:
            if os.path.exists(path):
                return path
        
        return None

def build_nodejs():
    """构建Node.js部分"""
    print("构建Node.js机器人...")
    
    # 检查 Node.js 环境
    if not check_nodejs_env():
        raise Exception("Node.js 环境检查失败")
    
    try:
        # 获取 npm 路径
        npm_path = get_npm_path()
        if not npm_path:
            raise Exception("找不到 npm，请确保 Node.js 正确安装")
        
        print(f"使用 npm 路径: {npm_path}")
        
        # 确保bot目录存在
        if not os.path.exists("bot"):
            os.makedirs("bot")
            # 创建基本的 package.json
            with open("bot/package.json", "w") as f:
                json.dump({
                    "name": "minecraft-ai-bot",
                    "version": "1.0.0",
                    "description": "Minecraft AI Bot",
                    "main": "index.js",
                    "scripts": {
                        "start": "node index.js"
                    },
                    "dependencies": {
                        "express": "^4.18.2",
                        "body-parser": "^1.20.2",
                        "mineflayer": "^4.8.1",
                        "mineflayer-collectblock": "^1.4.1",
                        "mineflayer-pathfinder": "^2.4.5",
                        "mineflayer-tool": "^1.2.0",
                        "prismarine-item": "^1.11.5",
                        "prismarine-viewer": "^1.23.0",
                        "vec3": "^0.1.7"
                    }
                }, f, indent=2)
        
        # 安装依赖
        print("安装Node.js依赖...")
        subprocess.run([npm_path, "install"], cwd="bot", check=True)
        
        # 创建构建目录
        build_dir = Path("build/bot")
        build_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        print("复制文件到构建目录...")
        for file in ["package.json", "index.js", "package-lock.json"]:
            src = Path("bot") / file
            if src.exists():
                shutil.copy2(src, build_dir)
                print(f"已复制: {file}")
        
        # 复制node_modules
        if os.path.exists("bot/node_modules"):
            print("复制node_modules...")
            shutil.copytree("bot/node_modules", build_dir / "node_modules", dirs_exist_ok=True)
        
        print("Node.js机器人构建完成")
        
    except subprocess.CalledProcessError as e:
        print(f"npm 命令执行失败: {e}")
        print(f"输出: {e.output.decode() if e.output else '无输出'}")
        raise
    except Exception as e:
        print(f"构建Node.js部分时出错: {e}")
        raise

def build_python():
    """构建Python部分"""
    print("构建Python应用...")
    
    # 创建spec文件
    spec_content = create_spec()
    with open("MinecraftAI.spec", "w") as f:
        f.write(spec_content)
    
    # 使用PyInstaller构建
    subprocess.run(["pyinstaller", "MinecraftAI.spec"], check=True)
    
    print("Python应用构建完成")

def create_release():
    """创建发布包"""
    print("创建发布包...")
    
    # 创建发布目录
    release_dir = Path("release/MinecraftAI")
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制可执行文件和配置
    shutil.copy2("dist/MinecraftAI.exe", release_dir)
    
    # 确保bot目录存在并包含所有必要文件
    bot_dir = release_dir / "bot"
    if os.path.exists("bot"):
        print("复制bot目录...")
        shutil.copytree("bot", bot_dir, dirs_exist_ok=True)
    else:
        print("创建bot目录...")
        bot_dir.mkdir(exist_ok=True)
        # 创建必要的文件
        create_bot_files(bot_dir)
    
    # 复制记忆文件（如果存在）
    if os.path.exists("memory.json"):
        shutil.copy2("memory.json", release_dir)
    
    # 复制资源目录
    resources_dir = release_dir / "resources"
    if os.path.exists("resources"):
        shutil.copytree("resources", resources_dir, dirs_exist_ok=True)
    
    # 创建启动脚本
    with open(release_dir / "start.bat", "w", encoding='utf-8') as f:
        f.write("""@echo off
echo 正在启动 Minecraft AI 助手...

:: 检查 Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Node.js，请先安装 Node.js
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

:: 检查配置文件
if not exist config.json (
    echo 错误: 未找到配置文件
    pause
    exit /b 1
)

:: 启动机器人服务器
cd bot
start /b cmd /c "npm install && npm start"
cd ..

:: 等待服务器启动
timeout /t 3

:: 启动主程序
start MinecraftAI.exe

:: 完成
echo 启动完成！
""")
    
    # 创建README
    with open(release_dir / "README.txt", "w", encoding='utf-8') as f:
        f.write("""Minecraft AI 助手使用说明

1. 安装要求：
   - Node.js (https://nodejs.org/)
   - Minecraft Java版

2. 配置说明：
   - 编辑 config.json 设置你的配置
   - 确保填写了正确的 DeepSeek API 密钥

3. 启动方法：
   - 双击 start.bat 启动程序
   - 或分别启动：
     1. 在 bot 目录运行: npm start
     2. 运行 MinecraftAI.exe

4. 故障排除：
   - 如果启动失败，检查配置文件是否正确
   - 确保 Node.js 已正确安装
   - 查看日志了解详细错误信息
""")
    
    print(f"发布包已创建在: {release_dir}")

def create_bot_files(bot_dir):
    """创建bot必要文件"""
    # 创建package.json
    with open(bot_dir / "package.json", "w") as f:
        json.dump({
            "name": "minecraft-ai-bot",
            "version": "1.0.0",
            "description": "Minecraft AI Bot",
            "main": "index.js",
            "scripts": {
                "start": "node index.js"
            },
            "dependencies": {
                "express": "^4.18.2",
                "body-parser": "^1.20.2",
                "mineflayer": "^4.8.1",
                "mineflayer-collectblock": "^1.4.1",
                "mineflayer-pathfinder": "^2.4.5",
                "mineflayer-tool": "^1.2.0",
                "prismarine-item": "^1.11.5",
                "prismarine-viewer": "^1.23.0",
                "vec3": "^0.1.7"
            }
        }, f, indent=2)
    
    # 复制其他必要文件
    if os.path.exists("bot/index.js"):
        shutil.copy2("bot/index.js", bot_dir)
    else:
        # 创建基本的index.js
        shutil.copy2("templates/bot/index.js", bot_dir)

def check_requirements():
    """检查必要的工具是否安装"""
    requirements_met = True
    
    # 检查Node.js
    try:
        node_version = subprocess.run(
            ["node", "--version"], 
            capture_output=True, 
            text=True
        ).stdout.strip()
        print(f"Node.js版本: {node_version}")
    except FileNotFoundError:
        print("错误: 未找到Node.js，请先安装Node.js")
        print("下载地址: https://nodejs.org/")
        requirements_met = False
    
    # 检查Python依赖
    try:
        import PIL
        print(f"Pillow版本: {PIL.__version__}")
    except ImportError:
        print("错误: 未找到Pillow库，正在尝试安装...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pillow"], check=True)
            print("Pillow安装成功")
        except Exception as e:
            print(f"Pillow安装失败: {e}")
            requirements_met = False
    
    return requirements_met

def main():
    """主构建流程"""
    try:
        print("检查环境要求...")
        if not check_requirements():
            print("\n请安装所需工具后重试")
            return
        
        print("\n开始构建...")
        
        # 构建资源
        from build_resources import create_resources
        create_resources()
        
        try:
            # 清理旧的构建文件
            for dir in ["build", "dist", "release"]:
                if os.path.exists(dir):
                    shutil.rmtree(dir)
            
            # 构建Node.js部分
            build_nodejs()
            
            # 构建Python部分
            build_python()
            
            # 创建发布包
            create_release()
            
            print("\n构建成功！发布包位于 release/MinecraftAI 目录")
            
        except Exception as e:
            print(f"\n构建过程出错: {e}")
            print("\n详细错误信息:")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 