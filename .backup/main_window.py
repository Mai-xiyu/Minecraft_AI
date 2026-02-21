from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QTextEdit, QLabel, QSpinBox, QLineEdit,
                           QGroupBox, QFormLayout, QTabWidget, QComboBox, QCheckBox, QDoubleSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer, QMetaObject, Q_ARG
import logging
import json
import sys
import time
from pathlib import Path
# Import i18n functions and DEFAULT_LANG
from .i18n import _, set_language, register_widget, update_ui_texts, get_current_language, DEFAULT_LANG
from gui.sponsor_page import SponsorPage
import os
import subprocess
import requests
from requests.exceptions import RequestException
import threading

# 添加版本号常量
VERSION = "1.2.7-By 饩雨(Mai xiyu)"

class LogHandler(logging.Handler):
    """自定义日志处理器，将日志发送到GUI"""
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        # Use a simple format, translation will happen in the GUI
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        # Emit the raw message or key. Formatting/translation happens in append_log
        msg = self.format(record)
        # Try to emit the log key and args if available
        log_key = getattr(record, 'log_key', None)
        log_args = getattr(record, 'log_args', {})
        if log_key:
            self.signal.emit((log_key, log_args))
        else:
            # Fallback for standard logging
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
    # Signal can now emit tuple (key, args) or str
    log_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()

        # --- Language Setup (Early) ---
        # Load language preference before setting up UI
        self.load_language_preference()
        # --- Store status keys ---
        self.current_connection_status_key = "status_not_connected"
        self.current_bot_status_key = "status_bot_not_started"
        # --- End Store status keys ---
        # --------------------------------

        # 修改标题，添加版本号 - Use i18n
        # self.setWindowTitle(f"Minecraft AI 控制面板 v{VERSION}") - Done via register_widget
        self.setMinimumSize(800, 600)
        
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 创建选项卡
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 控制面板选项卡
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab) # Pass parent widget here
        
        # 配置选项卡
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab) # Pass parent widget here
        
        # 添加赞助页面
        sponsor_tab = SponsorPage() # SponsorPage needs to be updated for i18n too
        
        # 添加控制面板组件
        self.setup_control_panel(control_layout)
        # control_tab.setLayout(control_layout) # Set the layout on the control tab widget - No longer needed
        
        # 添加配置面板组件
        self.setup_config_panel(config_layout)
        # config_tab.setLayout(config_layout) # Set the layout on the config tab widget - No longer needed
        
        # Add tabs after setup so widgets can be registered
        self.tabs.addTab(control_tab, "") # Placeholder text, will be set by update_ui_texts
        self.tabs.addTab(config_tab, "")
        self.tabs.addTab(sponsor_tab, "")
        
        # Register tab titles for translation
        register_widget(self.tabs, "control_tab", attr="tabText", index=0)
        register_widget(self.tabs, "config_tab", attr="tabText", index=1)
        register_widget(self.tabs, "sponsor_tab", attr="tabText", index=2)
        
        # Register window title
        register_widget(self, "window_title", attr="windowTitle", version=VERSION)
        
        # 设置日志处理
        self.setup_logging()
        
        # 加载配置 (loads language preference again, maybe redundant but safe)
        self.load_config()
        
        # 加载自定义任务
        self.load_custom_tasks()
        
        # Initial UI text update after all widgets are created and registered
        update_ui_texts()
        self.update_dynamic_texts() # Also update dynamic texts initially

    def setup_control_panel(self, layout):
        # 状态组
        self.status_group = QGroupBox()
        register_widget(self.status_group, "status_group", attr="title")
        status_layout = QFormLayout()
        
        # Connection Status
        self.status_label = QLabel() # Field widget
        # self.status_label.setText(_("status_not_connected")) # Initial text set below
        status_label_desc = QLabel() # Label widget - Create it empty
        register_widget(status_label_desc, "connection_status_label") # Register the LABEL
        status_layout.addRow(status_label_desc, self.status_label) # Add the widgets
        
        # Bot Status
        self.bot_status_label = QLabel() # Field widget
        # self.bot_status_label.setText(_("status_bot_not_started")) # Initial text set below
        bot_status_label_desc = QLabel() # Label widget - Create it empty
        register_widget(bot_status_label_desc, "bot_status_label") # Register the LABEL
        status_layout.addRow(bot_status_label_desc, self.bot_status_label) # Add the widgets
        
        # Set initial text for status labels using the stored keys
        self.status_label.setText(_(self.current_connection_status_key))
        self.bot_status_label.setText(_(self.current_bot_status_key))

        self.status_group.setLayout(status_layout)
        layout.addWidget(self.status_group)
        
        # 控制按钮组
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton()
        register_widget(self.start_button, "start_ai_button")
        self.start_button.clicked.connect(self.start_ai)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton()
        register_widget(self.stop_button, "stop_ai_button")
        self.stop_button.clicked.connect(self.stop_ai)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.test_conn_button = QPushButton()
        register_widget(self.test_conn_button, "test_connection_button")
        self.test_conn_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_conn_button)
        
        # 添加同步配置按钮
        self.sync_config_button = QPushButton()
        register_widget(self.sync_config_button, "sync_config_button")
        self.sync_config_button.clicked.connect(self.sync_config_to_bot)
        button_layout.addWidget(self.sync_config_button)
        
        # 添加模型下载按钮
        self.download_models_button = QPushButton()
        register_widget(self.download_models_button, "download_models_button")
        self.download_models_button.clicked.connect(self.download_vision_models)
        button_layout.addWidget(self.download_models_button)
        
        layout.addLayout(button_layout)
        
        # 日志显示
        log_group = QGroupBox()
        register_widget(log_group, "log_group", attr="title")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # 添加聊天组
        chat_group = QGroupBox()
        register_widget(chat_group, "chat_group", attr="title")
        chat_layout = QVBoxLayout()
        
        # 聊天显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)
        
        # 聊天输入区域
        chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        register_widget(self.chat_input, "chat_input_placeholder", attr="placeholderText")
        self.chat_input.returnPressed.connect(self.send_chat)
        chat_input_layout.addWidget(self.chat_input)
        
        send_button = QPushButton()
        register_widget(send_button, "send_button")
        send_button.clicked.connect(self.send_chat)
        chat_input_layout.addWidget(send_button)
        
        chat_layout.addLayout(chat_input_layout)
        chat_group.setLayout(chat_layout)
        layout.addWidget(chat_group)

    def setup_config_panel(self, layout):
        # Language Selection (Add this first or near the top)
        lang_layout = QHBoxLayout()
        lang_label = QLabel()
        register_widget(lang_label, "language_label")
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("中文", "zh")
        self.lang_combo.addItem("English", "en")
        # Connect signal AFTER initial population and language setting
        self.lang_combo.currentTextChanged.connect(self.language_changed)
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # Minecraft配置
        mc_group = QGroupBox()
        register_widget(mc_group, "minecraft_group", attr="title")
        mc_layout = QFormLayout()
        
        self.host_input = QLineEdit("localhost")
        mc_host_label = QLabel()
        register_widget(mc_host_label, "mc_host_label")
        mc_layout.addRow(mc_host_label, self.host_input)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(25565)
        mc_port_label = QLabel()
        register_widget(mc_port_label, "mc_port_label")
        mc_layout.addRow(mc_port_label, self.port_input)
        
        self.username_input = QLineEdit("AI_Player")
        mc_username_label = QLabel()
        register_widget(mc_username_label, "mc_username_label")
        mc_layout.addRow(mc_username_label, self.username_input)
        
        # 添加版本选择
        self.version_input = QComboBox()
        versions = ["1.21.1", "1.20.4", "1.20.2", "1.20.1", "1.19.4", "1.19.3", "1.19.2", "1.18.2", "1.17.1", "1.16.5"]
        self.version_input.addItems(versions)
        self.version_input.setEditable(True)  # 允许输入自定义版本
        mc_version_label = QLabel()
        register_widget(mc_version_label, "mc_version_label")
        mc_layout.addRow(mc_version_label, self.version_input)
        
        # 修改视距设置
        self.view_distance_input = QSpinBox()  # 改用QSpinBox而不是QComboBox
        self.view_distance_input.setRange(2, 32)  # 视距范围2-32个区块
        self.view_distance_input.setValue(8)  # 默认8个区块
        mc_view_distance_label = QLabel()
        register_widget(mc_view_distance_label, "mc_view_distance_label")
        mc_layout.addRow(mc_view_distance_label, self.view_distance_input)
        
        # 聊天长度限制
        self.chat_limit_input = QSpinBox()
        self.chat_limit_input.setRange(1, 256)
        self.chat_limit_input.setValue(100)
        mc_chat_limit_label = QLabel()
        register_widget(mc_chat_limit_label, "mc_chat_limit_label")
        mc_layout.addRow(mc_chat_limit_label, self.chat_limit_input)
        
        # 自动重连设置
        self.auto_reconnect = QCheckBox()
        self.auto_reconnect.setChecked(True)
        mc_auto_reconnect_label = QLabel()
        register_widget(mc_auto_reconnect_label, "mc_auto_reconnect_label")
        mc_layout.addRow(mc_auto_reconnect_label, self.auto_reconnect)
        
        # 重连延迟
        self.reconnect_delay = QSpinBox()
        self.reconnect_delay.setRange(1000, 60000)
        self.reconnect_delay.setValue(5000)
        self.reconnect_delay.setSuffix(" ms")
        mc_reconnect_delay_label = QLabel()
        register_widget(mc_reconnect_delay_label, "mc_reconnect_delay_label")
        mc_layout.addRow(mc_reconnect_delay_label, self.reconnect_delay)
        
        mc_group.setLayout(mc_layout)
        layout.addWidget(mc_group)
        
        # 添加服务器配置组
        server_group = QGroupBox()
        register_widget(server_group, "server_group", attr="title")
        server_layout = QFormLayout()
        
        self.server_host_input = QLineEdit("localhost")
        server_host_label = QLabel()
        register_widget(server_host_label, "server_host_label")
        server_layout.addRow(server_host_label, self.server_host_input)
        
        self.server_port_input = QSpinBox()
        self.server_port_input.setRange(1, 65535)
        self.server_port_input.setValue(3002)
        server_port_label = QLabel()
        register_widget(server_port_label, "server_port_label")
        server_layout.addRow(server_port_label, self.server_port_input)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # AI配置
        ai_group = QGroupBox()
        register_widget(ai_group, "ai_group", attr="title")
        ai_layout = QFormLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_label = QLabel()
        register_widget(api_key_label, "api_key_label")
        ai_layout.addRow(api_key_label, self.api_key_input)
        
        # 添加任务选择和保存组合
        task_layout = QHBoxLayout()
        
        self.task_input = QComboBox()
        tasks = [
            _("task_explore"), # Assuming keys like task_explore exist in i18n
            _("task_collect"),
            _("task_build"),
            _("task_farm"),
            _("task_mine"),
            _("task_craft"),
            _("task_combat"),
            _("task_free")
        ] # Need to define these keys in i18n.py
          # Let's keep the original task strings for now, as they seem to be keys used elsewhere
        tasks_keys_original = [
            "1. 探索世界", "2. 收集资源", "3. 建造房屋", "4. 种植农作物",
            "5. 挖矿", "6. 制作物品", "7. 战斗", "8. 自由行动"
        ]
        self.task_input.addItems(tasks_keys_original)
        self.task_input.setCurrentText("3. 建造房屋")
        self.task_input.setEditable(True)
        self.task_input.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)
        task_layout.addWidget(self.task_input)
        
        # 添加保存任务按钮
        save_task_btn = QPushButton()
        register_widget(save_task_btn, "save_task_button")
        register_widget(save_task_btn, "save_task_tooltip", attr="toolTip")
        save_task_btn.clicked.connect(self.save_custom_task)
        save_task_btn.setMaximumWidth(60)
        task_layout.addWidget(save_task_btn)
        
        ai_layout.addRow("初始任务:", task_layout)
        
        self.steps_input = QSpinBox()
        self.steps_input.setRange(1, 1000)
        self.steps_input.setValue(100)
        steps_label = QLabel()
        register_widget(steps_label, "steps_label")
        ai_layout.addRow(steps_label, self.steps_input)
        
        self.delay_input = QSpinBox()
        self.delay_input.setRange(1, 60)
        self.delay_input.setValue(2)
        delay_label = QLabel()
        register_widget(delay_label, "delay_label")
        ai_layout.addRow(delay_label, self.delay_input)
        
        # 添加温度设置
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0.1, 1.0)
        self.temperature_input.setValue(0.7)
        self.temperature_input.setSingleStep(0.1)
        temperature_label = QLabel()
        register_widget(temperature_label, "temperature_label")
        ai_layout.addRow(temperature_label, self.temperature_input)
        
        # 添加最大令牌数
        self.max_tokens_input = QSpinBox()
        self.max_tokens_input.setRange(100, 4096)
        self.max_tokens_input.setValue(2048)
        max_tokens_label = QLabel()
        register_widget(max_tokens_label, "max_tokens_label")
        ai_layout.addRow(max_tokens_label, self.max_tokens_input)
        
        # 添加复选框选项在一个组中
        options_group = QGroupBox()
        register_widget(options_group, "ai_options_group", attr="title")
        options_layout_container = QVBoxLayout() # Use a container layout
        options_group.setLayout(options_layout_container)

        # 创建选项布局
        options_checkbox_layout = QHBoxLayout() # Layout for checkboxes

        # 添加各种选项复选框
        self.use_local_model = QCheckBox()
        register_widget(self.use_local_model, "use_local_model_checkbox")
        options_checkbox_layout.addWidget(self.use_local_model)

        self.use_cache = QCheckBox()
        register_widget(self.use_cache, "use_cache_checkbox")
        self.use_cache.setChecked(True)  # 默认启用
        options_checkbox_layout.addWidget(self.use_cache)

        self.use_prediction = QCheckBox()
        register_widget(self.use_prediction, "use_prediction_checkbox")
        self.use_prediction.setChecked(True)  # 默认启用
        options_checkbox_layout.addWidget(self.use_prediction)

        # 将选项布局添加到主布局
        ai_layout.addRow("AI选项:", options_checkbox_layout)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        # 修改视觉系统配置组
        vision_group = QGroupBox()
        register_widget(vision_group, "vision_group", attr="title")
        vision_layout = QFormLayout()
        
        self.use_vision = QCheckBox()
        self.use_vision.setChecked(True)  # 默认启用
        vision_checkbox_label = QLabel()
        register_widget(vision_checkbox_label, "use_vision_checkbox")
        vision_layout.addRow(vision_checkbox_label, self.use_vision)
        
        # 替换简单的模型选择为包含详细信息的选择
        self.vision_model = QComboBox()
        # 清除现有项目
        self.vision_model.clear()
        # 添加带详细信息的项目
        self.vision_model.addItem(_("vision_model_resnet"), "ResNet18")
        self.vision_model.addItem(_("vision_model_mobilenet"), "MobileNet")
        self.vision_model.addItem(_("vision_model_custom"), "自定义")
        vision_model_label = QLabel()
        register_widget(vision_model_label, "vision_model_label")
        vision_layout.addRow(vision_model_label, self.vision_model)
        
        vision_group.setLayout(vision_layout)
        layout.addWidget(vision_group)
        
        # 保存按钮
        save_button = QPushButton()
        register_widget(save_button, "save_config_button")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

    def language_changed(self, text):
        lang_code = self.lang_combo.currentData()
        if lang_code:
            print(f"Language change requested: {text} ({lang_code})")
            set_language(lang_code)
            # Force immediate update of registered widgets
            update_ui_texts()
            # Update specific items not handled by registration if needed
            self.update_dynamic_texts() # Example: update vision model combo box text

    def update_dynamic_texts(self):
        """Update texts that might not be covered by simple registration."""
        # Example: Re-translate vision model combo box items
        current_data = self.vision_model.currentData()
        self.vision_model.blockSignals(True) # Prevent signal emission during update
        self.vision_model.clear()
        self.vision_model.addItem(_("vision_model_resnet"), "ResNet18")
        self.vision_model.addItem(_("vision_model_mobilenet"), "MobileNet")
        self.vision_model.addItem(_("vision_model_custom"), "自定义")
        # Restore selection
        index = self.vision_model.findData(current_data)
        if index != -1:
            self.vision_model.setCurrentIndex(index)
        self.vision_model.blockSignals(False)
        # Add other dynamic updates here if necessary

    def setup_logging(self):
        self.log_signal.connect(self.append_log)
        handler = LogHandler(self.log_signal)
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

        # Also configure our specific logger if needed
        self.logger = logging.getLogger("MinecraftAI.GUI")
        # self.logger.addHandler(handler) # Avoid duplicate handlers if root adds it
        self.logger.setLevel(logging.INFO)

    def append_log(self, message_data):
        # Check if it's a tuple (key, args) or just a string
        if isinstance(message_data, tuple) and len(message_data) == 2:
            key, args = message_data
            formatted_message = _(key, **args)
        elif isinstance(message_data, str):
            # Try to handle simple keys passed as string? Or just display raw?
            # Let's assume strings are already formatted or non-translatable
            formatted_message = message_data
        else:
            formatted_message = str(message_data) # Fallback

        self.log_text.append(formatted_message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def load_language_preference(self):
        """Load language preference from config before UI setup."""
        lang = DEFAULT_LANG # Default
        try:
            config_path = Path("config.json")
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    lang = config.get("gui", {}).get("language", DEFAULT_LANG)
        except Exception as e:
            print(f"Error loading language preference: {e}")
        # Set language using the loaded preference or default
        # This needs to happen before widgets are created if they are registered in setup methods
        set_language(lang)

    def load_config(self):
        try:
            config_path = Path("config.json")
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    
                # Load language first
                gui_config = config.get("gui", {})
                lang_code = gui_config.get("language", get_current_language()) # Use current if not found
                set_language(lang_code)
                # Update combo box selection without triggering signal
                index = self.lang_combo.findData(lang_code)
                if index != -1:
                    self.lang_combo.blockSignals(True)
                    self.lang_combo.setCurrentIndex(index)
                    self.lang_combo.blockSignals(False)

                # Load other configs...
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
                self.use_vision.setChecked(vision_config.get("use_vision", True))
                
                # 根据保存的模型值选择正确的项目
                model_value = vision_config.get("vision_model", "ResNet18")
                for i in range(self.vision_model.count()):
                    if self.vision_model.itemData(i) == model_value:
                        self.vision_model.setCurrentIndex(i)
                        break
                
                self.logger.info(_("log_config_loaded")) # Use translated log
            else:
                self.logger.info(_("log_default_config_created"))
                self.save_config() # Save default config (which includes default lang)
                # Ensure default lang is set in UI
                set_language(DEFAULT_LANG)
                index = self.lang_combo.findData(DEFAULT_LANG)
                if index != -1:
                    self.lang_combo.blockSignals(True)
                    self.lang_combo.setCurrentIndex(index)
                    self.lang_combo.blockSignals(False)

        except Exception as e:
            self.logger.error(_("log_config_load_failed", error=str(e)))
            # Attempt to save a default config on load failure too
            self.save_config()
            set_language(DEFAULT_LANG)
            index = self.lang_combo.findData(DEFAULT_LANG)
            if index != -1:
                self.lang_combo.blockSignals(True)
                self.lang_combo.setCurrentIndex(index)
                self.lang_combo.blockSignals(False)

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
            
            self.logger.info(_("log_config_saved"))
        except Exception as e:
            self.logger.error(_("log_config_save_failed", error=str(e)))

    def get_server_url(self):
        """获取服务器URL"""
        host = self.server_host_input.text()
        port = self.server_port_input.value()
        return f"http://{host}:{port}"

    def test_connection(self):
        self.test_conn_button.setEnabled(False)
        self.status_label.setText(_("status_connecting"))
        self.logger.info(_("log_test_connection_started"))

        self.conn_thread = ConnectionThread(
            f"{self.get_server_url()}/status",
            5
        )
        self.conn_thread.status_signal.connect(lambda msg_key: self.logger.info(_(msg_key)))
        self.conn_thread.finished_signal.connect(self.connection_finished)
        self.conn_thread.start()

    def connection_finished(self, success):
        self.test_conn_button.setEnabled(True)
        result_key = "log_test_connection_success" if success else "log_test_connection_failure"
        result_text = _(result_key)
        self.status_label.setText(_("status_connected") if success else _("status_connection_failed"))
        self.logger.info(_("log_test_connection_result", result=result_text))

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
            self.save_config()
            self.logger.info(_("log_config_saved")) # Config saved is already logged by save_config
            self.logger.info(_("log_ai_starting"))

            # Check server connection (internal logs might need translation if made visible)
            # server_url = f"{self.get_server_url()}/status"
            # if not self.test_server_connection(server_url): # This method logs internally
                 # bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot')
                 # log_msg = _("log_bot_server_not_detected", bot_dir=bot_dir)
                 # self.logger.error(log_msg)
                 # QMessageBox.critical(self, _("error_dialog_title"), log_msg)
                 # return # Stop if server not connected
                 # Let's allow starting AI even if server test fails, agent might handle connection

            # Create AI agent (agent logs internally, maybe pass logger or signal)
            from ai.agent import MinecraftAgent
            from ai.deepseek_api import DeepSeekAPI # Or choose based on config

            # Decide API or Local based on checkbox
            if self.use_local_model.isChecked():
                # Logic for local model instantiation if needed
                # Assuming MinecraftAgent handles local model logic internally based on env/config
                api_client = None # Or a local model client instance
                self.logger.info("Using local model (assumption: Agent handles this).")
            else:
                 api_client = DeepSeekAPI(self.api_key_input.text())
                 self.logger.info("Using DeepSeek API.")

            # Pass api_client (can be None for local model if Agent handles it)
            self.agent = MinecraftAgent(api_client)
            self.agent.set_task(self.task_input.currentText())

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.bot_status_label.setText(_("status_bot_running"))

            # Create AI Thread
            self.ai_thread = AIThread(self.agent, self.steps_input.value(), self.delay_input.value())
            # Connect log signal to handle translated logs
            self.ai_thread.log_signal.connect(self.append_log) # Already connected?
            # self.ai_thread.update_signal.connect(self.update_status)
            self.ai_thread.finished.connect(self.on_ai_finished)
            self.ai_thread.start()

            self.logger.info(_("log_ai_started"))

        except Exception as e:
            error_msg = _("log_ai_start_failed", error=str(e))
            self.logger.error(error_msg)
            QMessageBox.critical(self, _("error_dialog_title"), error_msg)
            self.stop_ai() # Ensure UI resets

    def start_bot_server(self):
        """Checks bot server connection, logs translated messages."""
        try:
            self.save_config() # Save latest config first
            # self.logger.info(_("log_config_saved")) # Already logged

            server_url = f"{self.get_server_url()}/status"
            if not self.test_server_connection(server_url):
                bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot')
                log_msg = _("log_bot_server_not_detected", bot_dir=bot_dir)
                self.logger.error(log_msg)
                raise Exception(log_msg) # Raise exception with translated message

            self.logger.info(_("log_server_connection_success"))

        except Exception as e:
            self.logger.error(f"{_('log_ai_start_failed', error=str(e))}") # Use generic start failed
            raise # Re-raise the exception

    def test_server_connection(self, url, max_attempts=5):
        """Tests server connection with translated logs."""
        for i in range(max_attempts):
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    self.logger.info(_("log_server_connection_success"))
                    return True
            except RequestException as e:
                 # Log simple connection error, avoid too much detail here
                 self.logger.debug(f"Connection attempt {i+1} failed: {e}")
                 pass # Fall through to retry message

            if i < max_attempts - 1:
                self.logger.info(_("log_server_connection_failed_retrying", attempt=i+1, max_attempts=max_attempts))
                time.sleep(2)

        # Log final failure after retries
        # self.logger.error(_("log_connection_error", error="Max retries reached")) # Or a specific message
        return False

    def stop_ai(self):
        """Stops the AI thread."""
        self.logger.info(_("log_ai_stopping"))
        try:
            if hasattr(self, 'ai_thread') and self.ai_thread.isRunning():
                self.ai_thread.terminate() # Use terminate for now, though join is safer
                self.ai_thread.wait() # Wait for thread to finish

            # Stop chat timer if exists
            if hasattr(self, 'chat_timer') and self.chat_timer.isActive():
                self.chat_timer.stop()

        except Exception as e:
            self.logger.error(_("log_ai_stop_failed", error=str(e)))
        finally:
             # Ensure UI is updated regardless of success/failure
             self._finish_stopping()

    def _check_thread_stopped(self):
        # This might not be needed if using terminate/wait or join
        pass

    def _finish_stopping(self):
        """Finalizes the stopping process and updates UI."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.bot_status_label.setText(_("status_bot_stopped"))
        self.agent = None
        self.logger.info(_("log_ai_stopped"))

    def on_ai_finished(self):
        """Called when AI thread finishes naturally."""
        self.logger.info(_("log_ai_completed"))
        self._finish_stopping()

    def sync_config_to_bot(self):
        self.logger.info(_("log_sync_config_started"))
        try:
            self.save_config() # Save latest config locally first

            server_url = f"{self.get_server_url()}/config"
            try:
                with open("config.json", "r") as f:
                    config_data = json.load(f)

                response = requests.post(server_url, json=config_data, timeout=5)

                if response.status_code == 200:
                    self.logger.info(_("log_sync_config_success"))
                else:
                    raise Exception(f"Server returned error: {response.status_code} - {response.text}")

            except requests.exceptions.ConnectionError:
                bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot')
                error_msg = _("log_bot_server_not_detected", bot_dir=bot_dir)
                self.logger.error(error_msg)
                QMessageBox.critical(self, _("error_dialog_title"), error_msg)
            except Exception as e:
                 # Catch other potential errors during sync process
                 error_msg = _("log_sync_config_failed", error=str(e))
                 self.logger.error(error_msg)
                 QMessageBox.critical(self, _("error_dialog_title"), error_msg)

        except Exception as e:
             # Catch errors during the initial save_config or URL generation
             error_msg = _("log_sync_config_failed", error=str(e))
             self.logger.error(error_msg)
             QMessageBox.critical(self, _("error_dialog_title"), error_msg)

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
                self.logger.info(_("log_custom_task_saved", task=custom_task))
            except Exception as e:
                self.logger.error(_("log_custom_task_save_failed", error=str(e)))

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
            self.logger.error(_("log_load_custom_tasks_failed", error=str(e)))

    def send_chat(self):
        message = self.chat_input.text().strip()
        if not message:
            return
        
        self.chat_input.clear()
        # Use translated "You"
        self.chat_display.append(f"<b>{_('chat_message_self')}:</b> {message}")
        
        try:
            server_url = self.get_server_url()
            response = requests.post(
                f"{server_url}/bot/chat",
                json={"message": message},
                timeout=5
            )
            
            if response.status_code != 200:
                self.chat_display.append(f"<span style='color:red'>{_('chat_send_failed')}</span>")
        except Exception as e:
            self.logger.error(f"{_('log_send_action_failed', error=str(e))}") # Generic send failed
            self.chat_display.append(f"<span style='color:red'>{_('chat_send_failed_network')}</span>")

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

    def update_status(self, update_data):
        """Update AI status display based on structured data from AIThread."""
        if not isinstance(update_data, dict):
             self.logger.warning(f"Received invalid status update data: {update_data}")
             return

        status = update_data.get('status')
        step = update_data.get('step')
        total = update_data.get('total')
        error = update_data.get('error')

        if status is False and error:
             self.bot_status_label.setText(_("status_bot_error"))
             # Optionally display the error somewhere specific
             # self.error_label.setText(_("log_ai_error", error=error))
             # self.error_label.setStyleSheet("color: red;")
             self.logger.error(_("log_ai_error", error=error))
        elif step is not None and total is not None:
             self.bot_status_label.setText(_("status_bot_running"))
             # Update step progress if you add a dedicated label for it
             # self.step_label.setText(_("log_ai_step", step=step, total=total))
             # Log step progress less frequently to avoid spamming
             if step % 5 == 0 or step == 1 or step == total:
                 self.logger.info(_("log_ai_step", step=step, total=total))
        elif self.bot_status_label.text() != _("status_bot_stopping"): # Avoid overriding stopping status
             self.bot_status_label.setText(_("status_bot_running")) # Default to running if no specific status

        # Clear error display if status is ok
        # if status is not False and hasattr(self, 'error_label') and self.error_label.text():
        #      self.error_label.setText("")

    def download_vision_models(self):
        self.logger.info(_("log_download_vision_models_started"))
        self.download_models_button.setEnabled(False)
        
        download_thread = threading.Thread(target=self._download_models_thread)
        download_thread.daemon = True
        download_thread.start()

    def _download_models_thread(self):
        log_queue = [] # Use a queue for thread-safe logging
        def thread_log(key, **kwargs):
            log_queue.append((key, kwargs))

        try:
            from ai.vision_learning import VisionLearningSystem # Assuming this exists
            # Pass the thread-safe logger to the system if it accepts one
            system = VisionLearningSystem(logger_func=thread_log)

            for model_name in system.MODEL_CONFIGS:
                thread_log("log_download_vision_model_downloading", model_name=model_name)
                local_path = system._download_model(model_name)
                thread_log("log_download_vision_model_saved", local_path=local_path)

            thread_log("log_download_vision_models_finished")
        except ImportError:
             thread_log("log_ai_error", error="VisionLearningSystem not found.") # Example error key
        except Exception as e:
            thread_log("log_download_vision_models_error", error=str(e))
        finally:
            # Process logs from the queue in the main thread
            while log_queue:
                key, kwargs = log_queue.pop(0)
                self.logger.info(_(key, **kwargs))
            # Re-enable button in main thread
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