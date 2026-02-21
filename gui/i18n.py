import json
import os
import sys
import weakref
from collections import defaultdict

# Try to import PyQt components needed for type checking (at top level)
try:
    from PyQt6.QtWidgets import (QWidget, QTabWidget, QLineEdit, QGroupBox,
                               QPushButton, QLabel, QCheckBox, QMainWindow,
                               QSpinBox, QComboBox)
    PYQT_AVAILABLE = True
except ImportError:
    # Define dummy classes if PyQt is not available
    class QWidget: pass
    class QTabWidget: pass
    class QLineEdit: pass
    class QGroupBox: pass
    class QPushButton: pass
    class QLabel: pass
    class QCheckBox: pass
    class QMainWindow: pass
    class QSpinBox: pass
    class QComboBox: pass
    PYQT_AVAILABLE = False
    print("警告：未找到 PyQt6。UI 翻译功能将受限。")

# 默认语言
DEFAULT_LANG = "zh"

translations = {
    "en": {
        # Main Window Titles & Tabs
        "window_title": "Minecraft AI Control Panel v{version}",
        "control_tab": "Control Panel",
        "config_tab": "Configuration",
        "sponsor_tab": "Support",
        "save_config_button": "Save Configuration",

        # Control Panel - Status Group
        "status_group": "System Status",
        "connection_status_label": "Connection Status:",
        "bot_status_label": "Bot Status:",
        "status_not_connected": "Not Connected",
        "status_connecting": "Connecting...",
        "status_connected": "Connected",
        "status_connection_failed": "Connection Failed",
        "status_bot_not_started": "Not Started",
        "status_bot_starting": "Starting...",
        "status_bot_running": "Running",
        "status_bot_stopping": "Stopping...",
        "status_bot_stopped": "Stopped",
        "status_bot_error": "Error",
        "status_empty_inventory": "(empty)",

        # Control Panel - Bot Server Buttons
        "start_bot_button": "Start Bot",
        "stop_bot_button": "Stop Bot",

        # Control Panel - Bot Info Panel
        "bot_info_group": "Bot Real-time Status",
        "bot_health_label": "Health:",
        "bot_food_label": "Hunger:",
        "bot_position_label": "Position:",
        "bot_inventory_label": "Inventory:",

        # Control Panel - Buttons
        "start_ai_button": "Start AI",
        "stop_ai_button": "Stop AI",
        "test_connection_button": "Test Connection",
        "test_llm_button": "Test LLM",
        "sync_config_button": "Sync Config",

        # Control Panel - Log Group
        "log_group": "System Log",

        # Control Panel - Runtime Task
        "runtime_task_placeholder": "Enter new task...",
        "change_task_button": "Change Task",

        # Control Panel - Chat Group
        "chat_group": "Chat",
        "chat_input_placeholder": "Enter message...",
        "send_button": "Send",
        "chat_message_self": "You",
        "chat_send_failed": "Send Failed",
        "chat_send_failed_network": "Send Failed: Network Error",

        # Config Panel - Minecraft Group
        "minecraft_group": "Minecraft Settings",
        "mc_host_label": "Server Address:",
        "mc_port_label": "Port:",
        "mc_username_label": "Username:",
        "mc_version_label": "Game Version:",
        "mc_view_distance_label": "View Distance (Chunks):",
        "mc_chat_limit_label": "Chat Length Limit:",
        "mc_auto_reconnect_label": "Auto Reconnect:",
        "mc_reconnect_delay_label": "Reconnect Delay:",

        # Config Panel - Server Group
        "server_group": "Bot Server Settings",
        "server_host_label": "Server Address:",
        "server_port_label": "Server Port:",

        # Config Panel - AI Group
        "ai_group": "AI Settings",
        "api_key_label": "API Key:",
        "base_url_label": "API Base URL:",
        "model_label": "Model:",
        "initial_task_label": "Initial Task:",
        "save_task_button": "Save",
        "save_task_tooltip": "Save current task to presets",
        "delay_label": "Step Delay (sec):",
        "temperature_label": "Temperature:",
        "max_tokens_label": "Max Tokens:",
        "ai_options_label": "AI Options:",
        "use_cache_checkbox": "Enable Cache",
        "use_prediction_checkbox": "Enable Prediction",

        # Config Panel - Language Selection
        "language_label": "Language:",

        # Sponsor Page
        "sponsor_title": "Support the Author",
        "sponsor_desc": "If this project is helpful to you, consider sponsoring!",
        "sponsor_alipay_button": "Alipay",
        "sponsor_wechat_button": "WeChat",
        "sponsor_qr_load_error": "Failed to load QR code",
        "sponsor_qr_not_found": "QR code not found",

        # Logging Messages (User Facing)
        "log_config_loaded": "Configuration loaded",
        "log_config_saved": "Configuration saved",
        "log_config_load_failed": "Failed to load configuration: {error}",
        "log_config_save_failed": "Failed to save configuration: {error}",
        "log_default_config_created": "Configuration file not found, creating default configuration",
        "log_test_connection_started": "Testing connection...",
        "log_test_connection_result": "Connection test {result}",
        "log_test_connection_success": "successful",
        "log_test_connection_failure": "failed",
        "log_sync_config_started": "Syncing configuration to bot server...",
        "log_sync_config_success": "Configuration synced to bot server",
        "log_sync_config_failed": "Failed to sync configuration: {error}",
        "log_bot_server_not_detected": """Bot server not detected, please start it manually:
1. Open command prompt
2. Navigate to: {bot_dir}
3. Run command: npm install
4. Run command: npm start""",
        "log_bot_starting": "Starting bot server...",
        "log_bot_stopping": "Stopping bot server...",
        "log_bot_ready": "Bot server is ready",
        "log_bot_already_running": "Bot server is already running",
        "log_ai_starting": "Starting AI...",
        "log_ai_start_failed": "Failed to start AI: {error}",
        "log_ai_started": "AI started",
        "log_ai_stopping": "Stopping AI...",
        "log_ai_stopped": "AI stopped",
        "log_ai_stop_failed": "Failed to stop AI: {error}",
        "log_ai_completed": "AI finished execution",
        "log_ai_step": "Executing step {step}/{total}",
        "log_ai_error": "AI execution error: {error}",
        "log_ai_exception": "AI execution exception: {error}",
        "log_ai_step_detail": "Step {step} [{status}]{action}{error}",
        "log_step_success": "Success",
        "log_step_failure": "Failure",
        "log_step_action": " | Action: {type}",
        "log_step_error": " | Error: {err}",
        "log_bot_waiting": "Waiting for bot server to be ready...",
        "log_bot_wait_timeout": "Timed out waiting for bot server",
        "log_task_changed": "Task changed to: {task}",
        "log_ai_not_running": "AI not running, cannot change task",
        "log_ai_auto_paused": "AI auto-paused: {reason}",
        "log_ai_step_infinite": "Step {step} [{status}]{action}{error}",
        "log_sync_started": "Syncing config...",
        "log_sync_done": "Config synced",
        "status_ai_paused": "Paused",
        "log_custom_task_saved": "Custom task saved: {task}",
        "log_custom_task_save_failed": "Failed to save custom task: {error}",
        "log_load_custom_tasks_failed": "Failed to load custom tasks: {error}",
        "log_get_bot_status_failed": "Failed to get bot status: {error}",
        "log_send_action_failed": "Failed to send action: {error}",
        "log_server_connection_failed_retrying": "Connection failed, retrying in 2 seconds... ({attempt}/{max_attempts})",
        "log_server_connection_success": "Successfully connected to bot server",
        "log_connecting_to_server": "Connecting to {url}...",
        "log_connection_error": "Connection error: {error}",

        # Dialogs
        "error_dialog_title": "Error",
        "llm_test_no_key": "Please enter an API Key first.",
        "llm_test_started": "Testing LLM connection...",
        "llm_test_success_title": "LLM Connection OK",
        "llm_test_fail_title": "LLM Connection Failed",
    },
    "zh": {
        # Main Window Titles & Tabs
        "window_title": "Minecraft AI 控制面板 v{version}",
        "control_tab": "控制面板",
        "config_tab": "配置",
        "sponsor_tab": "赞助支持",
        "save_config_button": "保存配置",

        # Control Panel - Status Group
        "status_group": "系统状态",
        "connection_status_label": "连接状态:",
        "bot_status_label": "机器人状态:",
        "status_not_connected": "未连接",
        "status_connecting": "正在连接...",
        "status_connected": "已连接",
        "status_connection_failed": "连接失败",
        "status_bot_not_started": "未启动",
        "status_bot_starting": "正在启动...",
        "status_bot_running": "运行中",
        "status_bot_stopping": "正在停止...",
        "status_bot_stopped": "已停止",
        "status_bot_error": "错误",
        "status_empty_inventory": "(空)",

        # Control Panel - Bot Server Buttons
        "start_bot_button": "启动Bot",
        "stop_bot_button": "停止Bot",

        # Control Panel - Bot Info Panel
        "bot_info_group": "机器人实时状态",
        "bot_health_label": "生命值:",
        "bot_food_label": "饥饿值:",
        "bot_position_label": "位置:",
        "bot_inventory_label": "物品栏:",

        # Control Panel - Buttons
        "start_ai_button": "启动AI",
        "stop_ai_button": "停止AI",
        "test_connection_button": "测试连接",
        "test_llm_button": "测试LLM",
        "sync_config_button": "同步配置",

        # Control Panel - Log Group
        "log_group": "系统日志",

        # Control Panel - Runtime Task
        "runtime_task_placeholder": "输入新任务...",
        "change_task_button": "切换任务",

        # Control Panel - Chat Group
        "chat_group": "聊天",
        "chat_input_placeholder": "输入消息...",
        "send_button": "发送",
        "chat_message_self": "你",
        "chat_send_failed": "发送失败",
        "chat_send_failed_network": "发送失败：网络错误",

        # Config Panel - Minecraft Group
        "minecraft_group": "Minecraft设置",
        "mc_host_label": "服务器地址:",
        "mc_port_label": "端口:",
        "mc_username_label": "用户名:",
        "mc_version_label": "游戏版本:",
        "mc_view_distance_label": "视距(区块):",
        "mc_chat_limit_label": "聊天长度限制:",
        "mc_auto_reconnect_label": "自动重连:",
        "mc_reconnect_delay_label": "重连延迟:",

        # Config Panel - Server Group
        "server_group": "机器人服务器设置",
        "server_host_label": "服务器地址:",
        "server_port_label": "服务器端口:",

        # Config Panel - AI Group
        "ai_group": "AI设置",
        "api_key_label": "API密钥:",
        "base_url_label": "API Base URL:",
        "model_label": "模型:",
        "initial_task_label": "初始任务:",
        "save_task_button": "保存",
        "save_task_tooltip": "保存当前任务到预设列表",
        "delay_label": "步骤延迟(秒):",
        "temperature_label": "温度:",
        "max_tokens_label": "最大令牌数:",
        "ai_options_label": "AI选项:",
        "use_cache_checkbox": "启用缓存",
        "use_prediction_checkbox": "启用预测",

        # Config Panel - Language Selection
        "language_label": "语言:",

        # Sponsor Page
        "sponsor_title": "支持作者",
        "sponsor_desc": "如果这个项目对你有帮助，欢迎赞助支持！",
        "sponsor_alipay_button": "支付宝",
        "sponsor_wechat_button": "微信",
        "sponsor_qr_load_error": "无法加载二维码",
        "sponsor_qr_not_found": "未找到二维码",

        # Logging Messages (User Facing)
        "log_config_loaded": "配置已加载",
        "log_config_saved": "配置已保存",
        "log_config_load_failed": "加载配置失败: {error}",
        "log_config_save_failed": "保存配置失败: {error}",
        "log_default_config_created": "未找到配置文件，创建默认配置",
        "log_test_connection_started": "正在测试连接...",
        "log_test_connection_result": "连接测试{result}",
        "log_test_connection_success": "成功",
        "log_test_connection_failure": "失败",
        "log_sync_config_started": "正在同步配置到机器人服务器...",
        "log_sync_config_success": "配置已同步到机器人服务器",
        "log_sync_config_failed": "同步配置失败: {error}",
        "log_bot_server_not_detected": """未检测到机器人服务器，请按以下步骤手动启动：
1. 打开命令提示符
2. 进入目录: {bot_dir}
3. 执行命令: npm install
4. 执行命令: npm start""",
        "log_bot_starting": "正在启动Bot服务器...",
        "log_bot_stopping": "正在停止Bot服务器...",
        "log_bot_ready": "Bot服务器已就绪",
        "log_bot_already_running": "Bot服务器已在运行中",
        "log_ai_starting": "正在启动AI...",
        "log_ai_start_failed": "启动AI失败: {error}",
        "log_ai_started": "AI已启动",
        "log_ai_stopping": "正在停止AI...",
        "log_ai_stopped": "AI已停止",
        "log_ai_stop_failed": "停止AI失败: {error}",
        "log_ai_completed": "AI已完成运行",
        "log_ai_step": "执行步骤 {step}/{total}",
        "log_ai_error": "AI执行错误: {error}",
        "log_ai_exception": "AI执行异常: {error}",
        "log_ai_step_detail": "步骤 {step} [{status}]{action}{error}",
        "log_step_success": "成功",
        "log_step_failure": "失败",
        "log_step_action": " | 动作: {type}",
        "log_step_error": " | 错误: {err}",
        "log_bot_waiting": "等待Bot服务器就绪...",
        "log_bot_wait_timeout": "等待Bot服务器超时",
        "log_task_changed": "任务已切换为: {task}",
        "log_ai_not_running": "AI未运行, 无法切换任务",
        "log_ai_auto_paused": "AI已自动暂停: {reason}",
        "log_ai_step_infinite": "步骤 {step} [{status}]{action}{error}",
        "log_sync_started": "正在同步配置...",
        "log_sync_done": "配置已同步",
        "status_ai_paused": "已暂停",
        "log_custom_task_saved": "自定义任务已保存: {task}",
        "log_custom_task_save_failed": "保存自定义任务失败: {error}",
        "log_load_custom_tasks_failed": "加载自定义任务失败: {error}",
        "log_get_bot_status_failed": "获取机器人状态失败: {error}",
        "log_send_action_failed": "发送动作失败: {error}",
        "log_server_connection_failed_retrying": "连接失败，2秒后重试... ({attempt}/{max_attempts})",
        "log_server_connection_success": "成功连接到机器人服务器",
        "log_connecting_to_server": "尝试连接到 {url}...",
        "log_connection_error": "连接错误: {error}",

        # Dialogs
        "error_dialog_title": "错误",
        "llm_test_no_key": "请先填写 API Key。",
        "llm_test_started": "正在测试 LLM 连接...",
        "llm_test_success_title": "LLM 连接成功",
        "llm_test_fail_title": "LLM 连接失败",
    }
}

current_language = DEFAULT_LANG
# 用于存储需要更新文本的控件引用
translatable_widgets = []

def set_language(lang):
    """设置当前语言并更新UI"""
    global current_language
    if lang in translations:
        current_language = lang
        print(f"Language set to: {current_language}")
        update_ui_texts() # Trigger UI update
    else:
        print(f"Warning: Language '{lang}' not found, using default '{current_language}'.")
        if current_language != DEFAULT_LANG:
             current_language = DEFAULT_LANG
             update_ui_texts()


def _(key, **kwargs):
    """获取当前语言的翻译文本"""
    lang_dict = translations.get(current_language, translations[DEFAULT_LANG]) # Fallback to default
    text = lang_dict.get(key, key) # Fallback to key itself if not found

    if isinstance(text, str):
        try:
            # 使用 format_map 以允许部分缺失的键
            return text.format_map(defaultdict(lambda: '', kwargs)) # Provide default for missing keys
        except Exception as e:
            # print(f"Warning: Error formatting translation for key '{key}' in language '{current_language}': {e}")
            # Fallback if format_map fails unexpectedly
            try:
                return text.format(**kwargs)
            except KeyError as ke:
                # print(f"Warning: Missing key '{ke}' during format for key '{key}'")
                return text # Return raw text if formatting fails due to missing key
            except Exception as final_e:
                # print(f"Warning: Final formatting attempt failed for key '{key}': {final_e}")
                return text
    return text # Return original if not a string

def register_widget(widget, key, attr="text", **kwargs):
    """注册需要翻译的控件"""
    # Avoid duplicates
    for item in translatable_widgets:
        if item["widget"] == widget and item["key"] == key and item["attr"] == attr:
            item["kwargs"] = kwargs # Update kwargs if already registered
            return
    translatable_widgets.append({"widget": widget, "key": key, "attr": attr, "kwargs": kwargs})

def update_ui_texts():
    """更新所有已注册控件的文本, 自动清理已销毁控件"""
    if not PYQT_AVAILABLE: return

    alive = []
    for item in translatable_widgets:
        widget = item["widget"]
        key = item["key"]
        attr = item["attr"]
        kwargs = item["kwargs"]
        translated_text = _(key, **kwargs)

        try:
            if widget is None:
                continue

            # 检查 Qt 控件是否已被销毁
            try:
                widget.objectName()
            except RuntimeError:
                # wrapped C/C++ object has been deleted
                continue

            alive.append(item)
            updated = False
            widget_type_name = type(widget).__name__

            # Check specific attribute/method combinations
            if attr == "tabText" and isinstance(widget, QTabWidget) and hasattr(widget, 'setTabText'):
                index = kwargs.get("index")
                if index is not None:
                    widget.setTabText(index, translated_text)
                    updated = True
                else:
                    print(f"警告：QTabWidget 键 '{key}' 的 kwargs 中缺少 'index'")
            elif attr == "windowTitle" and hasattr(widget, 'setWindowTitle'):
                widget.setWindowTitle(translated_text)
                updated = True
            elif attr == "title" and hasattr(widget, 'setTitle'): # Primarily for QGroupBox
                widget.setTitle(translated_text)
                updated = True
            elif attr == "placeholderText" and hasattr(widget, 'setPlaceholderText'): # Primarily for QLineEdit
                widget.setPlaceholderText(translated_text)
                updated = True
            elif attr == "toolTip" and hasattr(widget, 'setToolTip'):
                widget.setToolTip(translated_text)
                updated = True
            # Handle 'text' last as a common case for QLabel, QPushButton, QCheckBox etc.
            elif attr == "text" and hasattr(widget, 'setText'):
                widget.setText(translated_text)
                updated = True

            # Report if no specific handler was found and updated is still False
            if not updated:
                print(f"注意：无法为控件 {widget_type_name} (键: '{key}') 找到属性 '{attr}' 的处理方法")

        except Exception as e:
            print(f"更新控件文本时出错 键 '{key}' (控件: {widget_type_name}, 属性: {attr}): {e}")

    # 清理已销毁的控件引用
    translatable_widgets[:] = alive

def get_current_language():
    """获取当前设置的语言"""
    return current_language 