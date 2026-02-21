"""
Minecraft AI 控制面板 —— PyQt6 主窗口
重构版: 移除视觉系统, 使用通用 LLMClient
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QSpinBox, QLineEdit,
    QGroupBox, QFormLayout, QTabWidget, QComboBox, QCheckBox,
    QDoubleSpinBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
import logging
import json
import os
import subprocess
import signal
import time
from pathlib import Path
import requests
from requests.exceptions import RequestException

from .i18n import (
    _, set_language, register_widget, update_ui_texts,
    get_current_language, DEFAULT_LANG,
)
from gui.sponsor_page import SponsorPage

VERSION = "2.1.0-Improved"


# ─── 日志处理器 ──────────────────────────────────────────

class LogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)


# ─── 连接测试线程 ────────────────────────────────────────

class ConnectionThread(QThread):
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, url, attempts=5):
        super().__init__()
        self.url = url
        self.attempts = attempts

    def run(self):
        for i in range(self.attempts):
            try:
                resp = requests.get(self.url, timeout=3)
                if resp.status_code == 200:
                    self.finished_signal.emit(True)
                    return
            except Exception:
                pass
            if i < self.attempts - 1:
                time.sleep(1)
        self.finished_signal.emit(False)


# ─── 通用 HTTP 工作线程 ──────────────────────────────────

class HttpWorker(QThread):
    """在工作线程中执行 HTTP 请求, 避免阻塞主线程"""
    success = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, method: str, url: str, payload=None, timeout: int = 5):
        super().__init__()
        self.method = method.upper()
        self.url = url
        self.payload = payload
        self.timeout = timeout

    def run(self):
        try:
            if self.method == "GET":
                resp = requests.get(self.url, timeout=self.timeout)
            else:
                resp = requests.post(self.url, json=self.payload, timeout=self.timeout)
            self.success.emit(resp.json())
        except Exception as e:
            self.error.emit(str(e))


# ─── Bot 就绪等待线程 ────────────────────────────────────

class LLMTestWorker(QThread):
    """测试 LLM API 连接 (OpenAI 兼容接口)"""
    success = pyqtSignal(str)   # model reply snippet
    error = pyqtSignal(str)

    def __init__(self, base_url: str, api_key: str, model: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def run(self):
        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Say hello in one sentence."}],
                "max_tokens": 64,
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                reply = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                self.success.emit(
                    f"HTTP 200 OK | model={data.get('model', self.model)}\n"
                    f"Reply: {reply[:120]}"
                )
            else:
                self.error.emit(f"HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            self.error.emit(str(e))


class BotReadyWorker(QThread):
    """在工作线程中轮询 bot 服务器直到就绪或超时"""
    ready = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, url: str, max_attempts: int = 20):
        super().__init__()
        self.url = url
        self.max_attempts = max_attempts

    def run(self):
        for i in range(self.max_attempts):
            try:
                resp = requests.get(self.url, timeout=2)
                if resp.status_code == 200:
                    self.ready.emit()
                    return
            except Exception:
                pass
            time.sleep(1)
        self.failed.emit("Bot 服务器启动超时")


# ─── Bot 服务器进程管理线程 ──────────────────────────────

class BotServerThread(QThread):
    """管理 Node.js bot 子进程, 捕获 stdout/stderr 输出"""
    output_signal = pyqtSignal(str)
    ready_signal = pyqtSignal()
    stopped_signal = pyqtSignal()

    def __init__(self, bot_dir: str):
        super().__init__()
        self.bot_dir = bot_dir
        self.process: subprocess.Popen | None = None
        self._stopping = False

    def run(self):
        try:
            self.process = subprocess.Popen(
                ["node", "index.js"],
                cwd=self.bot_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace",
            )
            for line in iter(self.process.stdout.readline, ""):
                if self._stopping:
                    break
                stripped = line.rstrip()
                if stripped:
                    self.output_signal.emit(f"[Bot] {stripped}")
                if "服务器运行在" in stripped or "Server running" in stripped.lower():
                    self.ready_signal.emit()
            self.process.wait()
        except FileNotFoundError:
            self.output_signal.emit("[Bot] 错误: 未找到 node 命令, 请确保 Node.js 已安装并在 PATH 中")
        except Exception as e:
            self.output_signal.emit(f"[Bot] 进程异常: {e}")
        finally:
            self.stopped_signal.emit()

    def stop(self):
        self._stopping = True
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except Exception:
                pass


# ─── AI 运行线程 ─────────────────────────────────────────

class AIThread(QThread):
    log_signal = pyqtSignal(str)
    update_signal = pyqtSignal(dict)
    pause_signal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, agent, delay):
        super().__init__()
        self.agent = agent
        self.delay = delay
        self.running = True

    def run(self):
        step = 0
        try:
            while self.running:
                result = self.agent.step()

                # Agent 主动停止
                if result.get("stopped"):
                    break

                step += 1

                # 自动暂停检测
                if result.get("auto_paused"):
                    reason = result.get("error", "连续错误过多")
                    self.pause_signal.emit(reason)
                    break

                action_str = ""
                if result.get("action"):
                    action_str = _("log_step_action", type=result['action'].get('type', '?'))
                status_str = _("log_step_success") if result.get("success") else _("log_step_failure")
                error_str = _("log_step_error", err=result['error']) if result.get("error") else ""

                self.log_signal.emit(
                    _("log_ai_step_infinite", step=step,
                      status=status_str, action=action_str, error=error_str)
                )

                self.update_signal.emit({
                    "status": result.get("success", False),
                    "step": step,
                    "result": result,
                })

                time.sleep(self.delay)

            self.finished.emit()
        except Exception as e:
            self.log_signal.emit(_("log_ai_exception", error=str(e)))
            self.update_signal.emit({"status": False, "error": str(e)})
            self.finished.emit()

    def stop(self):
        self.running = False
        if self.agent:
            self.agent.request_stop()


# ─── 主窗口 ──────────────────────────────────────────────

class MainWindow(QMainWindow):
    log_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.agent = None
        self.ai_thread = None
        self.bot_server_thread = None
        self.status_timer = None
        self._poll_worker = None          # 状态轮询工作线程
        self._sync_worker = None          # 配置同步工作线程
        self._chat_worker = None          # 聊天发送工作线程
        self._bot_ready_worker = None     # Bot 就绪等待工作线程
        self._llm_test_worker = None      # LLM 测试工作线程

        self.load_language_preference()
        self.current_connection_status_key = "status_not_connected"
        self.current_bot_status_key = "status_bot_not_started"

        self.setMinimumSize(800, 600)

        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)

        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)

        sponsor_tab = SponsorPage()

        self.setup_control_panel(control_layout)
        self.setup_config_panel(config_layout)

        self.tabs.addTab(control_tab, "")
        self.tabs.addTab(config_tab, "")
        self.tabs.addTab(sponsor_tab, "")

        register_widget(self.tabs, "control_tab", attr="tabText", index=0)
        register_widget(self.tabs, "config_tab", attr="tabText", index=1)
        register_widget(self.tabs, "sponsor_tab", attr="tabText", index=2)
        register_widget(self, "window_title", attr="windowTitle", version=VERSION)

        self.setup_logging()
        self.load_config()
        self.load_custom_tasks()
        update_ui_texts()

    # ── 控制面板 ──────────────────────────────────────────

    def setup_control_panel(self, layout):
        # 状态组
        self.status_group = QGroupBox()
        register_widget(self.status_group, "status_group", attr="title")
        status_layout = QFormLayout()

        self.status_label = QLabel()
        status_label_desc = QLabel()
        register_widget(status_label_desc, "connection_status_label")
        status_layout.addRow(status_label_desc, self.status_label)

        self.bot_status_label = QLabel()
        bot_status_label_desc = QLabel()
        register_widget(bot_status_label_desc, "bot_status_label")
        status_layout.addRow(bot_status_label_desc, self.bot_status_label)

        self.status_label.setText(_(self.current_connection_status_key))
        self.bot_status_label.setText(_(self.current_bot_status_key))

        self.status_group.setLayout(status_layout)
        layout.addWidget(self.status_group)

        # Bot 服务器按钮
        bot_button_layout = QHBoxLayout()

        self.start_bot_button = QPushButton()
        register_widget(self.start_bot_button, "start_bot_button")
        self.start_bot_button.clicked.connect(self.start_bot_server)
        bot_button_layout.addWidget(self.start_bot_button)

        self.stop_bot_button = QPushButton()
        register_widget(self.stop_bot_button, "stop_bot_button")
        self.stop_bot_button.clicked.connect(self.stop_bot_server)
        self.stop_bot_button.setEnabled(False)
        bot_button_layout.addWidget(self.stop_bot_button)

        layout.addLayout(bot_button_layout)

        # Bot 实时状态面板
        self.bot_info_group = QGroupBox()
        register_widget(self.bot_info_group, "bot_info_group", attr="title")
        bot_info_layout = QFormLayout()

        self.bot_health_label = QLabel("--")
        bot_health_desc = QLabel()
        register_widget(bot_health_desc, "bot_health_label")
        bot_info_layout.addRow(bot_health_desc, self.bot_health_label)

        self.bot_food_label = QLabel("--")
        bot_food_desc = QLabel()
        register_widget(bot_food_desc, "bot_food_label")
        bot_info_layout.addRow(bot_food_desc, self.bot_food_label)

        self.bot_position_label = QLabel("--")
        bot_pos_desc = QLabel()
        register_widget(bot_pos_desc, "bot_position_label")
        bot_info_layout.addRow(bot_pos_desc, self.bot_position_label)

        self.bot_inventory_label = QLabel("--")
        bot_inv_desc = QLabel()
        register_widget(bot_inv_desc, "bot_inventory_label")
        bot_info_layout.addRow(bot_inv_desc, self.bot_inventory_label)

        self.bot_info_group.setLayout(bot_info_layout)
        layout.addWidget(self.bot_info_group)

        # AI 按钮
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

        self.test_llm_button = QPushButton()
        register_widget(self.test_llm_button, "test_llm_button")
        self.test_llm_button.clicked.connect(self.test_llm_connection)
        button_layout.addWidget(self.test_llm_button)

        self.sync_config_button = QPushButton()
        register_widget(self.sync_config_button, "sync_config_button")
        self.sync_config_button.clicked.connect(self.sync_config_to_bot)
        button_layout.addWidget(self.sync_config_button)

        layout.addLayout(button_layout)

        # 日志
        log_group = QGroupBox()
        register_widget(log_group, "log_group", attr="title")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # 运行时任务修改
        task_change_layout = QHBoxLayout()
        self.runtime_task_input = QLineEdit()
        register_widget(self.runtime_task_input, "runtime_task_placeholder", attr="placeholderText")
        self.runtime_task_input.returnPressed.connect(self.change_task_runtime)
        task_change_layout.addWidget(self.runtime_task_input)

        self.change_task_button = QPushButton()
        register_widget(self.change_task_button, "change_task_button")
        self.change_task_button.clicked.connect(self.change_task_runtime)
        self.change_task_button.setEnabled(False)
        task_change_layout.addWidget(self.change_task_button)
        layout.addLayout(task_change_layout)

        # 聊天
        chat_group = QGroupBox()
        register_widget(chat_group, "chat_group", attr="title")
        chat_layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)

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

    # ── 配置面板 ──────────────────────────────────────────

    def setup_config_panel(self, layout):
        # 语言切换
        lang_layout = QHBoxLayout()
        lang_label = QLabel()
        register_widget(lang_label, "language_label")
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("中文", "zh")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.currentTextChanged.connect(self.language_changed)
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # ── Minecraft 配置 ────────────────────────────────
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

        self.version_input = QComboBox()
        versions = [
            "1.21.1", "1.20.4", "1.20.2", "1.20.1",
            "1.19.4", "1.19.3", "1.19.2", "1.18.2", "1.17.1", "1.16.5",
        ]
        self.version_input.addItems(versions)
        self.version_input.setEditable(True)
        mc_version_label = QLabel()
        register_widget(mc_version_label, "mc_version_label")
        mc_layout.addRow(mc_version_label, self.version_input)

        self.view_distance_input = QSpinBox()
        self.view_distance_input.setRange(2, 32)
        self.view_distance_input.setValue(8)
        mc_view_distance_label = QLabel()
        register_widget(mc_view_distance_label, "mc_view_distance_label")
        mc_layout.addRow(mc_view_distance_label, self.view_distance_input)

        self.chat_limit_input = QSpinBox()
        self.chat_limit_input.setRange(1, 256)
        self.chat_limit_input.setValue(100)
        mc_chat_limit_label = QLabel()
        register_widget(mc_chat_limit_label, "mc_chat_limit_label")
        mc_layout.addRow(mc_chat_limit_label, self.chat_limit_input)

        self.auto_reconnect = QCheckBox()
        self.auto_reconnect.setChecked(True)
        mc_auto_reconnect_label = QLabel()
        register_widget(mc_auto_reconnect_label, "mc_auto_reconnect_label")
        mc_layout.addRow(mc_auto_reconnect_label, self.auto_reconnect)

        self.reconnect_delay = QSpinBox()
        self.reconnect_delay.setRange(1000, 60000)
        self.reconnect_delay.setValue(5000)
        self.reconnect_delay.setSuffix(" ms")
        mc_reconnect_delay_label = QLabel()
        register_widget(mc_reconnect_delay_label, "mc_reconnect_delay_label")
        mc_layout.addRow(mc_reconnect_delay_label, self.reconnect_delay)

        mc_group.setLayout(mc_layout)
        layout.addWidget(mc_group)

        # ── Bot 服务器配置 ────────────────────────────────
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

        # ── AI / LLM 配置 ────────────────────────────────
        ai_group = QGroupBox()
        register_widget(ai_group, "ai_group", attr="title")
        ai_layout = QFormLayout()

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_label = QLabel()
        register_widget(api_key_label, "api_key_label")
        ai_layout.addRow(api_key_label, self.api_key_input)

        # Base URL (新增)
        self.base_url_input = QLineEdit("https://api.deepseek.com/v1")
        base_url_label = QLabel()
        register_widget(base_url_label, "base_url_label")
        ai_layout.addRow(base_url_label, self.base_url_input)

        # Model (新增)
        self.model_input = QComboBox()
        self.model_input.addItems([
            "deepseek-chat", "deepseek-reasoner",
            "gpt-4o-mini", "gpt-4o",
            "qwen-plus", "qwen-turbo",
        ])
        self.model_input.setEditable(True)
        model_label = QLabel()
        register_widget(model_label, "model_label")
        ai_layout.addRow(model_label, self.model_input)

        # 任务
        task_layout = QHBoxLayout()
        self.task_input = QComboBox()
        tasks = [
            "1. 探索世界", "2. 收集资源", "3. 建造房屋", "4. 种植农作物",
            "5. 挖矿", "6. 制作物品", "7. 战斗", "8. 自由行动",
        ]
        self.task_input.addItems(tasks)
        self.task_input.setCurrentText("3. 建造房屋")
        self.task_input.setEditable(True)
        self.task_input.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)
        task_layout.addWidget(self.task_input)

        save_task_btn = QPushButton()
        register_widget(save_task_btn, "save_task_button")
        save_task_btn.clicked.connect(self.save_custom_task)
        save_task_btn.setMaximumWidth(60)
        task_layout.addWidget(save_task_btn)

        initial_task_label = QLabel()
        register_widget(initial_task_label, "initial_task_label")
        ai_layout.addRow(initial_task_label, task_layout)

        # 步间延迟 (步数已移除, AI 持续运行)
        self.delay_input = QSpinBox()
        self.delay_input.setRange(1, 60)
        self.delay_input.setValue(2)
        delay_label = QLabel()
        register_widget(delay_label, "delay_label")
        ai_layout.addRow(delay_label, self.delay_input)

        # 温度
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0.0, 2.0)
        self.temperature_input.setValue(0.7)
        self.temperature_input.setSingleStep(0.1)
        temperature_label = QLabel()
        register_widget(temperature_label, "temperature_label")
        ai_layout.addRow(temperature_label, self.temperature_input)

        # Max tokens
        self.max_tokens_input = QSpinBox()
        self.max_tokens_input.setRange(100, 8192)
        self.max_tokens_input.setValue(2048)
        max_tokens_label = QLabel()
        register_widget(max_tokens_label, "max_tokens_label")
        ai_layout.addRow(max_tokens_label, self.max_tokens_input)

        # 选项
        options_layout = QHBoxLayout()

        self.use_cache = QCheckBox()
        register_widget(self.use_cache, "use_cache_checkbox")
        self.use_cache.setChecked(True)
        options_layout.addWidget(self.use_cache)

        self.use_prediction = QCheckBox()
        register_widget(self.use_prediction, "use_prediction_checkbox")
        self.use_prediction.setChecked(True)
        options_layout.addWidget(self.use_prediction)

        ai_options_label = QLabel()
        register_widget(ai_options_label, "ai_options_label")
        ai_layout.addRow(ai_options_label, options_layout)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        # 保存按钮
        save_button = QPushButton()
        register_widget(save_button, "save_config_button")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

    # ── 语言切换 ──────────────────────────────────────────

    def language_changed(self, text):
        lang_code = self.lang_combo.currentData()
        if lang_code:
            set_language(lang_code)
            update_ui_texts()

    # ── 日志 ──────────────────────────────────────────────

    def setup_logging(self):
        self.log_signal.connect(self.append_log)
        handler = LogHandler(self.log_signal)

        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

        self.logger = logging.getLogger("MinecraftAI.GUI")
        self.logger.setLevel(logging.INFO)

    def append_log(self, message_data):
        if isinstance(message_data, tuple) and len(message_data) == 2:
            key, args = message_data
            text = _(key, **args)
        elif isinstance(message_data, str):
            text = message_data
        else:
            text = str(message_data)
        self.log_text.append(text)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    # ── 配置加载/保存 ────────────────────────────────────

    def load_language_preference(self):
        lang = DEFAULT_LANG
        try:
            p = Path("config.json")
            if p.exists():
                with open(p, "r") as f:
                    lang = json.load(f).get("gui", {}).get("language", DEFAULT_LANG)
        except Exception:
            pass
        set_language(lang)

    def load_config(self):
        try:
            p = Path("config.json")
            if not p.exists():
                self.save_config()
                return

            with open(p, "r") as f:
                config = json.load(f)

            # GUI
            gui_config = config.get("gui", {})
            lang_code = gui_config.get("language", get_current_language())
            set_language(lang_code)
            idx = self.lang_combo.findData(lang_code)
            if idx != -1:
                self.lang_combo.blockSignals(True)
                self.lang_combo.setCurrentIndex(idx)
                self.lang_combo.blockSignals(False)

            # Minecraft
            mc = config.get("minecraft", {})
            self.host_input.setText(mc.get("host", "localhost"))
            self.port_input.setValue(mc.get("port", 25565))
            self.username_input.setText(mc.get("username", "AI_Player"))
            self.version_input.setCurrentText(mc.get("version", "1.21.1"))
            self.view_distance_input.setValue(mc.get("viewDistance", 8))
            self.chat_limit_input.setValue(mc.get("chatLengthLimit", 100))
            self.auto_reconnect.setChecked(mc.get("autoReconnect", True))
            self.reconnect_delay.setValue(mc.get("reconnectDelay", 5000))

            # Server
            srv = config.get("server", {})
            self.server_host_input.setText(srv.get("host", "localhost"))
            self.server_port_input.setValue(srv.get("port", 3002))

            # AI
            ai = config.get("ai", {})
            self.api_key_input.setText(ai.get("api_key", ""))
            self.base_url_input.setText(ai.get("base_url", "https://api.deepseek.com/v1"))
            self.model_input.setCurrentText(ai.get("model", "deepseek-chat"))
            self.task_input.setCurrentText(ai.get("initial_task", "3. 建造房屋"))
            self.delay_input.setValue(ai.get("delay", 2))
            self.temperature_input.setValue(ai.get("temperature", 0.7))
            self.max_tokens_input.setValue(ai.get("max_tokens", 2048))
            self.use_cache.setChecked(ai.get("use_cache", True))
            self.use_prediction.setChecked(ai.get("use_prediction", True))

            self.logger.info(_("log_config_loaded"))
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")

    def save_config(self):
        try:
            config = {
                "minecraft": {
                    "host": self.host_input.text(),
                    "port": self.port_input.value(),
                    "username": self.username_input.text(),
                    "version": self.version_input.currentText(),
                    "viewDistance": self.view_distance_input.value(),
                    "chatLengthLimit": self.chat_limit_input.value(),
                    "autoReconnect": self.auto_reconnect.isChecked(),
                    "reconnectDelay": self.reconnect_delay.value(),
                },
                "server": {
                    "host": self.server_host_input.text(),
                    "port": self.server_port_input.value(),
                },
                "ai": {
                    "api_key": self.api_key_input.text(),
                    "base_url": self.base_url_input.text(),
                    "model": self.model_input.currentText(),
                    "initial_task": self.task_input.currentText(),
                    "delay": self.delay_input.value(),
                    "temperature": self.temperature_input.value(),
                    "max_tokens": self.max_tokens_input.value(),
                    "use_cache": self.use_cache.isChecked(),
                    "use_prediction": self.use_prediction.isChecked(),
                },
                "gui": {
                    "language": get_current_language(),
                },
            }
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
            self.logger.info(_("log_config_saved"))
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")

    # ── 网络操作 ──────────────────────────────────────────

    def get_server_url(self):
        host = self.server_host_input.text()
        port = self.server_port_input.value()
        return f"http://{host}:{port}"

    def test_connection(self):
        self.test_conn_button.setEnabled(False)
        self.status_label.setText(_("status_connecting"))
        self.logger.info(_("log_test_connection_started"))

        self.conn_thread = ConnectionThread(f"{self.get_server_url()}/status")
        self.conn_thread.finished_signal.connect(self.connection_finished)
        self.conn_thread.start()

    def connection_finished(self, success):
        self.test_conn_button.setEnabled(True)
        if success:
            self.status_label.setText(_("status_connected"))
            self.logger.info("连接成功")
        else:
            self.status_label.setText(_("status_connection_failed"))
            self.logger.warning("连接失败")

    def test_llm_connection(self):
        """测试 LLM API 连接"""
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        model = self.model_input.currentText().strip()
        if not api_key:
            QMessageBox.warning(self, _("error_dialog_title"), _("llm_test_no_key"))
            return
        self.test_llm_button.setEnabled(False)
        self.logger.info(_("llm_test_started"))
        self._llm_test_worker = LLMTestWorker(base_url, api_key, model)
        self._llm_test_worker.success.connect(self._on_llm_test_success)
        self._llm_test_worker.error.connect(self._on_llm_test_error)
        self._llm_test_worker.start()

    def _on_llm_test_success(self, msg):
        self.test_llm_button.setEnabled(True)
        self.logger.info(f"LLM 连接成功: {msg}")
        QMessageBox.information(self, _("llm_test_success_title"), msg)

    def _on_llm_test_error(self, err):
        self.test_llm_button.setEnabled(True)
        self.logger.error(f"LLM 连接失败: {err}")
        QMessageBox.critical(self, _("llm_test_fail_title"), err)

    def sync_config_to_bot(self):
        self.logger.info(_("log_sync_config_started"))
        self.sync_config_button.setEnabled(False)
        try:
            self.save_config()
            with open("config.json", "r") as f:
                config_data = json.load(f)
            self._sync_worker = HttpWorker("POST", f"{self.get_server_url()}/config", payload=config_data, timeout=5)
            self._sync_worker.success.connect(self._on_sync_success)
            self._sync_worker.error.connect(self._on_sync_error)
            self._sync_worker.start()
        except Exception as e:
            self.sync_config_button.setEnabled(True)
            self.logger.error(f"同步失败: {e}")
            QMessageBox.critical(self, _("error_dialog_title"), str(e))

    def _on_sync_success(self, data):
        self.sync_config_button.setEnabled(True)
        self.logger.info(_("log_sync_config_success"))

    def _on_sync_error(self, err):
        self.sync_config_button.setEnabled(True)
        self.logger.error(f"同步失败: {err}")
        QMessageBox.critical(self, _("error_dialog_title"), err)

    # ── AI 控制 ──────────────────────────────────────────

    def start_ai(self):
        try:
            self.save_config()
            self.logger.info(_("log_ai_starting"))
            self.start_button.setEnabled(False)

            # 自动启动 bot 服务器 (如果未运行)
            if not (self.bot_server_thread and self.bot_server_thread.isRunning()):
                self.start_bot_server()

            # 在工作线程中等待 bot 就绪, 完成后回调 _on_bot_ready_for_ai
            self.logger.info(_("log_bot_waiting"))
            self._bot_ready_worker = BotReadyWorker(f"{self.get_server_url()}/status", max_attempts=20)
            self._bot_ready_worker.ready.connect(self._on_bot_ready_for_ai)
            self._bot_ready_worker.failed.connect(self._on_bot_ready_failed)
            self._bot_ready_worker.start()

        except Exception as e:
            self.logger.error(f"启动失败: {e}")
            QMessageBox.critical(self, _("error_dialog_title"), str(e))
            self._finish_stopping()

    def _on_bot_ready_for_ai(self):
        """Bot 就绪后, 在主线程中创建 Agent 和 AIThread"""
        try:
            with open("config.json", "r") as f:
                config = json.load(f)

            ai_cfg = config.get("ai", {})

            from ai.llm_client import LLMClient
            from ai.agent import MinecraftAgent

            llm = LLMClient(
                api_key=ai_cfg.get("api_key", ""),
                base_url=ai_cfg.get("base_url", "https://api.deepseek.com/v1"),
                model=ai_cfg.get("model", "deepseek-chat"),
                temperature=ai_cfg.get("temperature", 0.7),
                max_tokens=ai_cfg.get("max_tokens", 2048),
            )

            self.agent = MinecraftAgent(config, llm)
            self.agent.set_task(ai_cfg.get("initial_task", "自由行动"))

            self.stop_button.setEnabled(True)
            self.change_task_button.setEnabled(True)
            self.bot_status_label.setText(_("status_bot_running"))

            self.ai_thread = AIThread(
                self.agent,
                ai_cfg.get("delay", 2),
            )
            self.ai_thread.log_signal.connect(self.append_log)
            self.ai_thread.update_signal.connect(self.update_status)
            self.ai_thread.pause_signal.connect(self._on_ai_paused)
            self.ai_thread.finished.connect(self.on_ai_finished)
            self.ai_thread.start()

            self.logger.info(_("log_ai_started"))
        except Exception as e:
            self.logger.error(f"启动失败: {e}")
            QMessageBox.critical(self, _("error_dialog_title"), str(e))
            self._finish_stopping()

    def _on_bot_ready_failed(self, reason):
        """Bot 就绪超时"""
        self.logger.error(_("log_bot_wait_timeout"))
        QMessageBox.critical(self, _("error_dialog_title"), reason)
        self._finish_stopping()

    def _on_ai_paused(self, reason):
        """AI 自动暂停时的处理"""
        self.logger.warning(_("log_ai_auto_paused", reason=reason))
        self.bot_status_label.setText(_("status_ai_paused"))
        QMessageBox.warning(self, _("error_dialog_title"), reason)

    def stop_ai(self):
        self.logger.info(_("log_ai_stopping"))
        try:
            if self.ai_thread and self.ai_thread.isRunning():
                self.ai_thread.stop()
                self.ai_thread.wait(5000)
            if self.agent:
                self.agent.shutdown()
        except Exception as e:
            self.logger.error(f"停止异常: {e}")
        finally:
            self._finish_stopping()

    def on_ai_finished(self):
        self.logger.info(_("log_ai_completed"))
        if self.agent:
            self.agent.shutdown()
        self._finish_stopping()

    def _finish_stopping(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.change_task_button.setEnabled(False)
        self.bot_status_label.setText(_("status_bot_stopped"))
        self.agent = None
        self.ai_thread = None

    def update_status(self, data):
        if not isinstance(data, dict):
            return
        if data.get("status") is False and data.get("error"):
            self.bot_status_label.setText(_("status_bot_error"))

    # ── Bot 服务器管理 ─────────────────────────────────────

    def start_bot_server(self):
        """启动 Node.js bot 子进程"""
        if self.bot_server_thread and self.bot_server_thread.isRunning():
            self.logger.warning(_("log_bot_already_running"))
            return

        bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bot")
        if not os.path.exists(os.path.join(bot_dir, "index.js")):
            self.logger.error(f"Bot 目录不存在: {bot_dir}")
            return

        self.logger.info(_("log_bot_starting"))
        self.start_bot_button.setEnabled(False)
        self.stop_bot_button.setEnabled(True)
        self.bot_status_label.setText(_("status_bot_starting"))

        self.bot_server_thread = BotServerThread(bot_dir)
        self.bot_server_thread.output_signal.connect(self.append_log)
        self.bot_server_thread.ready_signal.connect(self._on_bot_ready)
        self.bot_server_thread.stopped_signal.connect(self._on_bot_stopped)
        self.bot_server_thread.start()

    def stop_bot_server(self):
        """停止 Node.js bot 子进程"""
        if self.bot_server_thread and self.bot_server_thread.isRunning():
            self.logger.info(_("log_bot_stopping"))
            self.bot_server_thread.stop()
            self.bot_server_thread.wait(8000)
        self._on_bot_stopped()

    def _on_bot_ready(self):
        self.bot_status_label.setText(_("status_bot_running"))
        self.status_label.setText(_("status_connected"))
        self.logger.info(_("log_bot_ready"))
        # 启动状态轮询定时器
        self._start_status_polling()

    def _on_bot_stopped(self):
        self.start_bot_button.setEnabled(True)
        self.stop_bot_button.setEnabled(False)
        self.bot_status_label.setText(_("status_bot_stopped"))
        self._stop_status_polling()

    # ── Bot 状态轮询 ─────────────────────────────────────

    def _start_status_polling(self):
        if self.status_timer is None:
            self.status_timer = QTimer(self)
            self.status_timer.timeout.connect(self._poll_bot_status)
        self.status_timer.start(5000)

    def _stop_status_polling(self):
        if self.status_timer:
            self.status_timer.stop()
        self.bot_health_label.setText("--")
        self.bot_food_label.setText("--")
        self.bot_position_label.setText("--")
        self.bot_inventory_label.setText("--")

    def _poll_bot_status(self):
        # 如果上一个轮询 worker 还在运行, 跳过本轮
        if self._poll_worker and self._poll_worker.isRunning():
            return
        self._poll_worker = HttpWorker("GET", f"{self.get_server_url()}/bot/status", timeout=3)
        self._poll_worker.success.connect(self._on_poll_result)
        self._poll_worker.error.connect(lambda _: None)  # 静默
        self._poll_worker.start()

    def _on_poll_result(self, data):
        try:
            if data.get("connected") and data.get("state"):
                state = data["state"]
                hp = state.get("health", 0)
                food = state.get("food", 0)
                pos = state.get("position")
                inv = state.get("inventory", [])

                self.bot_health_label.setText(f"{hp}/20")
                self.bot_food_label.setText(f"{food}/20")
                if pos:
                    self.bot_position_label.setText(
                        f"({pos.get('x', 0):.1f}, {pos.get('y', 0):.1f}, {pos.get('z', 0):.1f})"
                    )
                inv_summary = ", ".join(f"{i['name']}x{i['count']}" for i in inv[:5])
                self.bot_inventory_label.setText(inv_summary or _("status_empty_inventory"))
            else:
                self.bot_health_label.setText("--")
        except Exception:
            pass

    # ── 运行时任务修改 ────────────────────────────────────

    def change_task_runtime(self):
        new_task = self.runtime_task_input.text().strip()
        if not new_task:
            return
        if self.agent:
            self.agent.set_task(new_task)
            self.logger.info(_("log_task_changed", task=new_task))
            self.runtime_task_input.clear()
        else:
            self.logger.warning(_("log_ai_not_running"))

    # ── 窗口关闭事件 ─────────────────────────────────────

    def closeEvent(self, event):
        """窗口关闭时清理所有资源"""
        # 停止 AI
        if self.ai_thread and self.ai_thread.isRunning():
            self.ai_thread.stop()
            self.ai_thread.wait(3000)
        if self.agent:
            try:
                self.agent.shutdown()
            except Exception:
                pass

        # 停止状态轮询
        self._stop_status_polling()

        # 停止 bot 服务器
        if self.bot_server_thread and self.bot_server_thread.isRunning():
            self.bot_server_thread.stop()
            self.bot_server_thread.wait(5000)

        event.accept()

    # ── 聊天 ─────────────────────────────────────────────

    def send_chat(self):
        message = self.chat_input.text().strip()
        if not message:
            return
        self.chat_input.clear()
        self.chat_display.append(f"<b>{_('chat_message_self')}:</b> {message}")
        self._chat_worker = HttpWorker("POST", f"{self.get_server_url()}/bot/chat",
                                       payload={"message": message}, timeout=5)
        self._chat_worker.success.connect(
            lambda data: None if data.get("success") else self.chat_display.append(
                f"<span style='color:red'>{_('chat_send_failed')}</span>")
        )
        self._chat_worker.error.connect(
            lambda err: self.chat_display.append(
                f"<span style='color:red'>{_('chat_send_failed_network')}: {err}</span>")
        )
        self._chat_worker.start()

    # ── 自定义任务 ────────────────────────────────────────

    def save_custom_task(self):
        task = self.task_input.currentText()
        if not task.strip():
            return
        found = any(
            self.task_input.itemText(i) == task
            for i in range(self.task_input.count())
        )
        if not found:
            self.task_input.addItem(task)
            try:
                with open("custom_tasks.txt", "a", encoding="utf-8") as f:
                    f.write(f"{task}\n")
                self.logger.info(f"已保存自定义任务: {task}")
            except Exception as e:
                self.logger.error(f"保存任务失败: {e}")

    def load_custom_tasks(self):
        try:
            if os.path.exists("custom_tasks.txt"):
                with open("custom_tasks.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        task = line.strip()
                        if task and not any(
                            task == self.task_input.itemText(i)
                            for i in range(self.task_input.count())
                        ):
                            self.task_input.addItem(task)
        except Exception:
            pass
