from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QTextEdit, QLabel, QSpinBox, QLineEdit,
                           QGroupBox, QFormLayout, QTabWidget, QComboBox, QCheckBox, QDoubleSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer, QMetaObject, Q_ARG
import logging
import json
import sys
import time
from pathlib import Path
from gui.sponsor_page import SponsorPage
import os
import subprocess
import requests
from requests.exceptions import RequestException
import threading

# 添加版本号常量
VERSION = "1.2.0-By Mai-xiyu"

class LogHandler(logging.Handler):
    """自定义日志处理器，将日志发送到GUI"""
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)

class ConnectionThread(QThread):
    """连接测试线程"""
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, url, attempts):
        super().__init__()
        self.url = url
        self.attempts = attempts

    def run(self):
        try:
            # 尝试导入 test_connection
            try:
                from test_connection import test_connection
            except ImportError:
                # 如果导入失败，创建一个简单的内部测试函数
                def test_connection(url, attempts):
                    self.status_signal.emit(f"尝试连接到 {url}...")
                    try:
                        import requests
                        for i in range(attempts):
                            try:
                                response = requests.get(url, timeout=2)
                                if response.status_code == 200:
                                    return True
                            except Exception:
                                pass
                            if i < attempts - 1:
                                time.sleep(1)
                        return False
                    except ImportError:
                        self.status_signal.emit("错误：未安装requests库")
                        return False
            
            result = test_connection(self.url, self.attempts)
            self.finished_signal.emit(result)
        except Exception as e:
            self.status_signal.emit(f"连接错误: {e}")
            self.finished_signal.emit(False)

class AIThread(QThread):
    """AI运行线程"""
    log_signal = pyqtSignal(str)
    update_signal = pyqtSignal(dict)  # 添加状态更新信号
    finished = pyqtSignal()  # 添加完成信号
    
    def __init__(self, agent, steps, delay):
        super().__init__()
        self.agent = agent
        self.steps = steps
        self.delay = delay
        self.running = True
    
    def run(self):
        try:
            for i in range(self.steps):
                if not self.running:
                    break
                    
                # 执行一步并获取结果
                result = self.agent.step()
                
                # 发送日志消息
                self.log_signal.emit(f"执行步骤 {i+1}/{self.steps}")
                
                # 同时发送结构化状态更新
                self.update_signal.emit({
                    'status': True,
                    'step': i+1,
                    'total': self.steps,
                    'result': result
                })
                
                time.sleep(self.delay)
                
            # 完成后发送信号
            self.finished.emit()
        except Exception as e:
            error_msg = f"AI执行错误: {e}"
            self.log_signal.emit(error_msg)
            # 发送错误状态
            self.update_signal.emit({'status': False, 'error': str(e)})
            self.finished.emit()
    
    def terminate(self):
        self.running = False
        super().terminate()

class MainWindow(QMainWindow):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # 修改标题，添加版本号
        self.setWindowTitle(f"Minecraft AI 控制面板 v{VERSION}")
        self.setMinimumSize(800, 600)
        
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 创建选项卡
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # 控制面板选项卡
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)
        tabs.addTab(control_tab, "控制面板")
        
        # 配置选项卡
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)
        tabs.addTab(config_tab, "配置")
        
        # 添加赞助页面
        sponsor_tab = SponsorPage()
        tabs.addTab(sponsor_tab, "赞助支持")
        
        # 添加控制面板组件
        self.setup_control_panel(control_layout)
        
        # 添加配置面板组件
        self.setup_config_panel(config_layout)
        
        # 设置日志处理
        self.setup_logging()
        
        # 加载配置
        self.load_config()
        
        # 加载自定义任务
        self.load_custom_tasks()

    def setup_control_panel(self, layout):
        # 状态组
        status_group = QGroupBox("系统状态")
        status_layout = QFormLayout()
        
        self.status_label = QLabel("未连接")
        status_layout.addRow("连接状态:", self.status_label)
        
        self.bot_status_label = QLabel("未启动")
        status_layout.addRow("机器人状态:", self.bot_status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 控制按钮组
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("启动AI")
        self.start_button.clicked.connect(self.start_ai)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止AI")
        self.stop_button.clicked.connect(self.stop_ai)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.test_conn_button = QPushButton("测试连接")
        self.test_conn_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_conn_button)
        
        # 添加同步配置按钮
        self.sync_config_button = QPushButton("同步配置")
        self.sync_config_button.clicked.connect(self.sync_config_to_bot)
        button_layout.addWidget(self.sync_config_button)
        
        # 添加模型下载按钮
        self.download_models_button = QPushButton("下载视觉模型")
        self.download_models_button.clicked.connect(self.download_vision_models)
        button_layout.addWidget(self.download_models_button)
        
        layout.addLayout(button_layout)
        
        # 日志显示
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # 添加聊天组
        chat_group = QGroupBox("聊天")
        chat_layout = QVBoxLayout()
        
        # 聊天显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)
        
        # 聊天输入区域
        chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("输入消息...")
        self.chat_input.returnPressed.connect(self.send_chat)
        chat_input_layout.addWidget(self.chat_input)
        
        send_button = QPushButton("发送")
        send_button.clicked.connect(self.send_chat)
        chat_input_layout.addWidget(send_button)
        
        chat_layout.addLayout(chat_input_layout)
        chat_group.setLayout(chat_layout)
        layout.addWidget(chat_group)

    def setup_config_panel(self, layout):
        # Minecraft配置
        mc_group = QGroupBox("Minecraft设置")
        mc_layout = QFormLayout()
        
        self.host_input = QLineEdit("localhost")
        mc_layout.addRow("服务器地址:", self.host_input)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(25565)
        mc_layout.addRow("端口:", self.port_input)
        
        self.username_input = QLineEdit("AI_Player")
        mc_layout.addRow("用户名:", self.username_input)
        
        # 添加版本选择
        self.version_input = QComboBox()
        versions = ["1.21.1", "1.20.4", "1.20.2", "1.20.1", "1.19.4", "1.19.3", "1.19.2", "1.18.2", "1.17.1", "1.16.5"]
        self.version_input.addItems(versions)
        self.version_input.setEditable(True)  # 允许输入自定义版本
        mc_layout.addRow("游戏版本:", self.version_input)
        
        # 修改视距设置
        self.view_distance_input = QSpinBox()  # 改用QSpinBox而不是QComboBox
        self.view_distance_input.setRange(2, 32)  # 视距范围2-32个区块
        self.view_distance_input.setValue(8)  # 默认8个区块
        mc_layout.addRow("视距(区块):", self.view_distance_input)
        
        # 聊天长度限制
        self.chat_limit_input = QSpinBox()
        self.chat_limit_input.setRange(1, 256)
        self.chat_limit_input.setValue(100)
        mc_layout.addRow("聊天长度限制:", self.chat_limit_input)
        
        # 自动重连设置
        self.auto_reconnect = QCheckBox()
        self.auto_reconnect.setChecked(True)
        mc_layout.addRow("自动重连:", self.auto_reconnect)
        
        # 重连延迟
        self.reconnect_delay = QSpinBox()
        self.reconnect_delay.setRange(1000, 60000)
        self.reconnect_delay.setValue(5000)
        self.reconnect_delay.setSuffix(" ms")
        mc_layout.addRow("重连延迟:", self.reconnect_delay)
        
        mc_group.setLayout(mc_layout)
        layout.addWidget(mc_group)
        
        # 添加服务器配置组
        server_group = QGroupBox("服务器设置")
        server_layout = QFormLayout()
        
        self.server_host_input = QLineEdit("localhost")
        server_layout.addRow("服务器地址:", self.server_host_input)
        
        self.server_port_input = QSpinBox()
        self.server_port_input.setRange(1, 65535)
        self.server_port_input.setValue(3002)
        server_layout.addRow("服务器端口:", self.server_port_input)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # AI配置
        ai_group = QGroupBox("AI设置")
        ai_layout = QFormLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        ai_layout.addRow("API密钥:", self.api_key_input)
        
        # 添加任务选择和保存组合
        task_layout = QHBoxLayout()
        
        self.task_input = QComboBox()
        tasks = [
            "1. 探索世界",
            "2. 收集资源",
            "3. 建造房屋",
            "4. 种植农作物",
            "5. 挖矿",
            "6. 制作物品",
            "7. 战斗",
            "8. 自由行动"
        ]
        self.task_input.addItems(tasks)
        self.task_input.setCurrentText("3. 建造房屋")  # 默认任务
        self.task_input.setEditable(True)  # 设置为可编辑
        self.task_input.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)  # 新输入项添加到底部
        task_layout.addWidget(self.task_input)
        
        # 添加保存任务按钮
        save_task_btn = QPushButton("保存")
        save_task_btn.setToolTip("保存当前任务到预设列表")
        save_task_btn.clicked.connect(self.save_custom_task)
        save_task_btn.setMaximumWidth(60)
        task_layout.addWidget(save_task_btn)
        
        ai_layout.addRow("初始任务:", task_layout)
        
        self.steps_input = QSpinBox()
        self.steps_input.setRange(1, 1000)
        self.steps_input.setValue(100)
        ai_layout.addRow("执行步数:", self.steps_input)
        
        self.delay_input = QSpinBox()
        self.delay_input.setRange(1, 60)
        self.delay_input.setValue(2)
        ai_layout.addRow("步骤延迟(秒):", self.delay_input)
        
        # 添加温度设置
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0.1, 1.0)
        self.temperature_input.setValue(0.7)
        self.temperature_input.setSingleStep(0.1)
        ai_layout.addRow("温度:", self.temperature_input)
        
        # 添加最大令牌数
        self.max_tokens_input = QSpinBox()
        self.max_tokens_input.setRange(100, 4096)
        self.max_tokens_input.setValue(2048)
        ai_layout.addRow("最大令牌数:", self.max_tokens_input)
        
        # 添加复选框选项在一个组中
        options_group = QGroupBox("AI选项")
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)

        # 创建选项布局
        options_layout = QHBoxLayout()

        # 添加各种选项复选框
        self.use_local_model = QCheckBox("使用本地模型")
        options_layout.addWidget(self.use_local_model)

        self.use_cache = QCheckBox("启用缓存")
        self.use_cache.setChecked(True)  # 默认启用
        options_layout.addWidget(self.use_cache)

        self.use_prediction = QCheckBox("启用预测")
        self.use_prediction.setChecked(True)  # 默认启用
        options_layout.addWidget(self.use_prediction)

        self.use_vision = QCheckBox("启用视觉")
        self.use_vision.setChecked(True)  # 默认启用
        options_layout.addWidget(self.use_vision)

        # 将选项布局添加到主布局
        ai_layout.addRow("AI选项:", options_layout)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        # 修改视觉系统配置组
        vision_group = QGroupBox("视觉系统")
        vision_layout = QFormLayout()
        
        self.use_vision = QCheckBox()
        self.use_vision.setChecked(False)
        vision_layout.addRow("启用视觉:", self.use_vision)
        
        # 替换简单的模型选择为包含详细信息的选择
        self.vision_model = QComboBox()
        # 清除现有项目
        self.vision_model.clear()
        # 添加带详细信息的项目
        self.vision_model.addItem("ResNet18 (18M参数|44MB|适合GPU)", "ResNet18")
        self.vision_model.addItem("MobileNet (4M参数|14MB|手机/CPU)", "MobileNet")
        self.vision_model.addItem("自定义模型 (可导入专业模型)", "自定义")
        vision_layout.addRow("视觉模型:", self.vision_model)
        
        vision_group.setLayout(vision_layout)
        layout.addWidget(vision_group)
        
        # 保存按钮
        save_button = QPushButton("保存配置")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

    def setup_logging(self):
        # 设置日志处理器
        self.log_signal.connect(self.append_log)
        handler = LogHandler(self.log_signal)
        
        # 配置根日志记录器
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def append_log(self, message):
        self.log_text.append(message)
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def load_config(self):
        try:
            config_path = Path("config.json")
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    
                # 加载Minecraft配置
                mc_config = config.get("minecraft", {})
                self.host_input.setText(mc_config.get("host", "localhost"))
                self.port_input.setValue(mc_config.get("port", 25565))
                self.username_input.setText(mc_config.get("username", "AI_Player"))
                
                # 加载新增的Minecraft配置
                self.version_input.setCurrentText(mc_config.get("version", "1.21.1"))
                self.view_distance_input.setValue(mc_config.get("viewDistance", 8))
                self.chat_limit_input.setValue(mc_config.get("chatLengthLimit", 100))
                self.auto_reconnect.setChecked(mc_config.get("autoReconnect", True))
                self.reconnect_delay.setValue(mc_config.get("reconnectDelay", 5000))
                
                # 加载服务器配置
                server_config = config.get("server", {})
                self.server_host_input.setText(server_config.get("host", "localhost"))
                self.server_port_input.setValue(server_config.get("port", 3002))
                
                # 加载AI配置
                ai_config = config.get("ai", {})
                self.api_key_input.setText(ai_config.get("api_key", ""))
                self.task_input.setCurrentText(ai_config.get("initial_task", "3. 建造房屋"))
                self.steps_input.setValue(ai_config.get("steps", 100))
                self.delay_input.setValue(ai_config.get("delay", 2))
                self.temperature_input.setValue(ai_config.get("temperature", 0.7))
                self.max_tokens_input.setValue(ai_config.get("max_tokens", 2048))
                
                # 加载视觉系统配置
                vision_config = config.get("vision", {})
                self.use_vision.setChecked(vision_config.get("use_vision", False))
                
                # 根据保存的模型值选择正确的项目
                model_value = vision_config.get("vision_model", "ResNet18")
                for i in range(self.vision_model.count()):
                    if self.vision_model.itemData(i) == model_value:
                        self.vision_model.setCurrentIndex(i)
                        break
                
                logging.info("配置已加载")
            else:
                # 如果配置文件不存在，创建默认配置并保存
                logging.info("未找到配置文件，创建默认配置")
                self.save_config()
                
        except Exception as e:
            logging.error(f"加载配置失败: {e}")
            # 发生错误时也创建默认配置
            self.save_config()

    def save_config(self):
        try:
            config = {
                "deepseek_api_key": self.api_key_input.text(),
                "minecraft": {
                    "host": self.host_input.text(),
                    "port": self.port_input.value(),
                    "username": self.username_input.text(),
                    "version": self.version_input.currentText(),
                    "viewDistance": self.view_distance_input.value(),  # 使用数字而不是字符串
                    "chatLengthLimit": self.chat_limit_input.value(),
                    "autoReconnect": self.auto_reconnect.isChecked(),
                    "reconnectDelay": self.reconnect_delay.value()
                },
                "ai": {
                    "api_key": self.api_key_input.text(),
                    "initial_task": self.task_input.currentText(),
                    "steps": self.steps_input.value(),
                    "delay": self.delay_input.value(),
                    "temperature": self.temperature_input.value(),
                    "max_tokens": self.max_tokens_input.value(),
                    "memory_capacity": 20,
                    "learning_enabled": True
                },
                "server": {
                    "host": self.server_host_input.text(),
                    "port": self.server_port_input.value()
                },
                "vision": {
                    "use_vision": self.use_vision.isChecked(),
                    "vision_model": self.vision_model.currentData(),  # 使用数据值而不是显示文本
                }
            }
            
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            logging.info("配置已保存")
        except Exception as e:
            logging.error(f"保存配置失败: {e}")

    def get_server_url(self):
        """获取服务器URL"""
        host = self.server_host_input.text()
        port = self.server_port_input.value()
        return f"http://{host}:{port}"

    def test_connection(self):
        self.test_conn_button.setEnabled(False)
        self.status_label.setText("正在测试连接...")
        
        # 使用配置的服务器地址
        self.conn_thread = ConnectionThread(
            f"{self.get_server_url()}/status",
            5
        )
        self.conn_thread.status_signal.connect(lambda msg: logging.info(msg))
        self.conn_thread.finished_signal.connect(self.connection_finished)
        self.conn_thread.start()

    def connection_finished(self, success):
        self.test_conn_button.setEnabled(True)
        self.status_label.setText("已连接" if success else "连接失败")

    def check_server_connection(self, max_retries=3):
        """检查服务器连接状态"""
        server_url = self.get_server_url()
        
        for i in range(max_retries):
            try:
                response = requests.get(f"{server_url}/bot/status", timeout=10)
                if response.status_code == 200:
                    return True
                
                time.sleep(1)  # 失败后等待1秒再重试
            except Exception as e:
                logging.warning(f"连接服务器失败 (尝试 {i+1}/{max_retries}): {e}")
                time.sleep(2)  # 失败后等待2秒再重试
            
        return False

    def start_ai(self):
        try:
            # 1. 保存最新配置
            self.save_config()
            logging.info("已更新配置文件")
            
            # 2. 检查机器人服务器连接
            server_url = f"{self.get_server_url()}/status"
            if not self.test_server_connection(server_url):
                raise Exception("无法连接到机器人服务器")
            
            # 3. 创建AI代理
            from ai.agent import MinecraftAgent
            from ai.deepseek_api import DeepSeekAPI
            
            # 创建API客户端
            api = DeepSeekAPI(self.api_key_input.text())
            
            # 创建AI代理
            self.agent = MinecraftAgent(api)
            # 设置当前任务
            self.agent.current_task = self.task_input.currentText()
            
            # 4. 启动AI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.bot_status_label.setText("运行中")
            
            # 创建AI运行线程
            self.ai_thread = AIThread(self.agent, self.steps_input.value(), self.delay_input.value())
            self.ai_thread.log_signal.connect(lambda msg: logging.info(msg))
            self.ai_thread.update_signal.connect(self.update_status)  # 连接update_signal到update_status方法
            self.ai_thread.finished.connect(self.on_ai_finished)  # 连接完成信号
            self.ai_thread.start()
            
            logging.info("AI已启动")
            
        except Exception as e:
            logging.error(f"启动AI失败: {e}")
            self.stop_ai()

    def start_bot_server(self):
        """检查机器人服务器连接"""
        try:
            # 保存最新配置
            self.save_config()
            logging.info("配置已更新")
            
            # 检查服务器连接
            server_url = f"{self.get_server_url()}/status"
            if not self.test_server_connection(server_url):
                # 如果连接失败，提示用户手动启动服务器
                bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot')
                logging.error(f"""
未检测到机器人服务器，请按以下步骤手动启动：
1. 打开命令提示符
2. 进入目录: {bot_dir}
3. 执行命令: npm install
4. 执行命令: npm start
                """)
                raise Exception("请先手动启动机器人服务器")
            
            logging.info("成功连接到机器人服务器")
            
        except Exception as e:
            logging.error(f"启动失败: {e}")
            raise

    def test_server_connection(self, url, max_attempts=5):
        """测试服务器连接"""
        for i in range(max_attempts):
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    logging.info("成功连接到机器人服务器")
                    return True
            except RequestException:
                pass
            
            if i < max_attempts - 1:
                logging.info(f"连接失败，2秒后重试... ({i+1}/{max_attempts})")
                time.sleep(2)
        
        return False

    def stop_ai(self):
        """停止AI"""
        try:
            # 停止AI线程
            if hasattr(self, 'ai_thread') and self.ai_thread.isRunning():
                # 先设置停止标志
                self.ai_thread.running = False
                
                # 创建一个定时器来检查线程是否结束
                self.stop_timer = QTimer()
                self.stop_timer.timeout.connect(self._check_thread_stopped)
                self.stop_timer.start(100)  # 每100ms检查一次
                
                # 禁用按钮，直到完全停止
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(False)
                self.bot_status_label.setText("正在停止...")
                
            else:
                self._finish_stopping()
                
            # 停止聊天更新
            if hasattr(self, 'chat_timer'):
                self.chat_timer.stop()
                
        except Exception as e:
            logging.error(f"停止AI失败: {e}")
            self._finish_stopping()

    def _check_thread_stopped(self):
        """检查线程是否已经停止"""
        if not self.ai_thread.isRunning():
            self.stop_timer.stop()
            self._finish_stopping()

    def _finish_stopping(self):
        """完成停止过程"""
        # 重置状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.bot_status_label.setText("已停止")
        self.agent = None
        
        logging.info("AI已停止")

    def on_ai_finished(self):
        """AI线程完成时调用"""
        try:
            # 恢复界面状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("状态: 已停止")
            
            # 记录日志
            logging.info("AI已完成运行")
        except Exception as e:
            logging.error(f"处理AI完成事件时出错: {e}")

    def sync_config_to_bot(self):
        """同步配置到机器人服务器"""
        try:
            # 保存最新配置
            self.save_config()
            
            # 使用配置的服务器地址
            server_url = f"{self.get_server_url()}/config"
            try:
                # 读取配置文件
                with open("config.json", "r") as f:
                    config = json.load(f)
                
                # 发送配置到服务器
                response = requests.post(
                    server_url,
                    json=config,
                    timeout=5
                )
                
                if response.status_code == 200:
                    logging.info("配置已同步到机器人服务器")
                else:
                    raise Exception(f"服务器返回错误: {response.status_code}")
                
            except requests.exceptions.ConnectionError:
                bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot')
                raise Exception(f"""
未检测到机器人服务器，请先启动服务器：
1. 打开命令提示符
2. 进入目录: {bot_dir}
3. 执行命令: npm install
4. 执行命令: npm start
                """)
            except Exception as e:
                raise Exception(f"同步配置失败: {e}")
            
        except Exception as e:
            logging.error(str(e))
            # 可以在这里添加错误提示对话框
            QMessageBox.critical(self, "错误", str(e))

    def save_custom_task(self):
        custom_task = self.task_input.currentText()
        
        # 检查是否已存在
        found = False
        for i in range(self.task_input.count()):
            if self.task_input.itemText(i) == custom_task:
                found = True
                break
        
        # 如果不存在，添加到列表
        if not found and custom_task.strip():
            self.task_input.addItem(custom_task)
            
            # 保存到本地文件
            try:
                tasks_file = "custom_tasks.txt"
                with open(tasks_file, "a+", encoding="utf-8") as f:
                    f.seek(0)  # 先定位到文件开头
                    existing_tasks = f.read().splitlines()
                    if custom_task not in existing_tasks:
                        f.write(f"{custom_task}\n")
                logging.info(f"自定义任务已保存: {custom_task}")
            except Exception as e:
                logging.error(f"保存自定义任务失败: {e}")

    def load_custom_tasks(self):
        try:
            tasks_file = "custom_tasks.txt"
            if os.path.exists(tasks_file):
                with open(tasks_file, "r", encoding="utf-8") as f:
                    custom_tasks = f.read().splitlines()
                    for task in custom_tasks:
                        if task.strip() and not any(task == self.task_input.itemText(i) for i in range(self.task_input.count())):
                            self.task_input.addItem(task)
        except Exception as e:
            logging.error(f"加载自定义任务失败: {e}")

    def send_chat(self):
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # 清除输入框
        self.chat_input.clear()
        
        # 显示消息到聊天窗口
        self.chat_display.append(f"<b>你:</b> {message}")
        
        # 发送到机器人
        try:
            server_url = self.get_server_url()
            response = requests.post(
                f"{server_url}/bot/chat",
                json={"message": message},
                timeout=5
            )
            
            if response.status_code != 200:
                self.chat_display.append("<span style='color:red'>发送失败</span>")
        except Exception as e:
            logging.error(f"发送聊天消息失败: {e}")
            self.chat_display.append("<span style='color:red'>发送失败: 网络错误</span>")

    def update_chat(self):
        try:
            server_url = self.get_server_url()
            response = requests.get(
                f"{server_url}/bot/chat/history",
                timeout=2
            )
            
            if response.status_code == 200:
                messages = response.json()
                
                # 只显示新消息
                if not hasattr(self, 'last_message_id'):
                    self.last_message_id = 0
                    
                for msg in messages:
                    if msg['id'] > self.last_message_id:
                        if msg['source'] == 'player':
                            # 玩家消息已由send_chat方法添加
                            pass
                        else:
                            # AI或其他玩家的消息
                            self.chat_display.append(f"<b>{msg['username']}:</b> {msg['message']}")
                        self.last_message_id = msg['id']
        except Exception as e:
            pass  # 静默失败，避免频繁错误消息

    def update_status(self, step_count, status, error=None):
        """更新AI状态显示"""
        self.step_label.setText(f"步骤: {step_count}")
        self.status_label.setText(f"状态: {status}")
        
        # 如果有任务队列，显示它们
        if hasattr(self.ai_thread, 'task_queue') and self.ai_thread.task_queue:
            task_count = len(self.ai_thread.task_queue)
            
            # 获取当前执行的任务信息
            current_task = "未知任务"
            if hasattr(self.ai_thread, 'current_plan'):
                current_task = self.ai_thread.current_plan
            
            # 创建任务队列信息
            task_queue_text = f"\n执行计划: {current_task}\n"
            task_queue_text += f"剩余任务: {task_count}\n"
            
            for i, task in enumerate(self.ai_thread.task_queue[:3]):  # 只显示前3个任务
                desc = task.get('description', f"任务 {i+1}")
                action = task.get('action', 'unknown')
                task_queue_text += f"- {desc} ({action})\n"
            
            if task_count > 3:
                task_queue_text += f"... 还有 {task_count-3} 个任务\n"
            
            self.log_text.append(task_queue_text)
        
        if error:
            self.error_label.setText(f"错误: {error}")
            self.error_label.setStyleSheet("color: red;")
        else:
            self.error_label.setText("")

    def download_vision_models(self):
        """手动下载视觉模型"""
        self.log_text.append("开始下载视觉模型...")
        self.download_models_button.setEnabled(False)
        
        # 创建后台线程下载模型
        download_thread = threading.Thread(target=self._download_models_thread)
        download_thread.daemon = True
        download_thread.start()

    def _download_models_thread(self):
        """后台下载模型的线程"""
        try:
            from ai.vision_learning import VisionLearningSystem
            system = VisionLearningSystem()
            
            # 强制下载所有模型
            for model_name in system.MODEL_CONFIGS:
                self.log_text.append(f"下载模型: {model_name}")
                local_path = system._download_model(model_name)
                self.log_text.append(f"模型已保存到: {local_path}")
            
            self.log_text.append("所有视觉模型下载完成!")
        except Exception as e:
            self.log_text.append(f"下载模型时出错: {e}")
        finally:
            # 修复连接类型
            QMetaObject.invokeMethod(self.download_models_button, "setEnabled", 
                                   Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))

# 修改OutputReader类，添加启动完成信号
class OutputReader(QObject):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    server_started = pyqtSignal()  # 新增服务器启动信号
    
    def __init__(self, process):
        super().__init__()
        self.process = process
        self.running = True
        self.server_ready = False
    
    def read_output(self):
        while self.running:
            output = self.process.stdout.readline()
            if output:
                output = output.strip()
                self.output_received.emit(output)
                # 检查服务器是否已启动
                if not self.server_ready and "服务器运行在" in output:
                    self.server_ready = True
                    self.server_started.emit()
            error = self.process.stderr.readline()
            if error:
                self.error_received.emit(error.strip())
            if not output and not error and self.process.poll() is not None:
                break
    
    def stop(self):
        self.running = False 