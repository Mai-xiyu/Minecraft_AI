from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
                           QStackedWidget)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os
from pathlib import Path
import sys
# Import i18n functions
from .i18n import _, register_widget

class SponsorPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        # Note: update_ui_texts() in MainWindow handles the initial update
        # No need to call it explicitly here unless this widget is created standalone
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel()
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        register_widget(title, "sponsor_title") # Register for translation
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 说明文字
        desc = QLabel()
        desc.setStyleSheet("font-size: 16px; margin: 10px;")
        register_widget(desc, "sponsor_desc") # Register for translation
        layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        # 支付宝按钮
        self.alipay_btn = QPushButton()
        register_widget(self.alipay_btn, "sponsor_alipay_button") # Register
        self.alipay_btn.setStyleSheet("""
            QPushButton {
                background-color: #1677FF;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4096FF;
            }
            QPushButton:pressed {
                background-color: #0958D9;
            }
            QPushButton:checked {
                background-color: #0958D9;
            }
        """)
        self.alipay_btn.setCheckable(True)
        self.alipay_btn.setChecked(True)
        self.alipay_btn.clicked.connect(lambda: self.switch_qr('alipay'))
        button_layout.addWidget(self.alipay_btn)
        
        # 微信按钮
        self.wechat_btn = QPushButton()
        register_widget(self.wechat_btn, "sponsor_wechat_button") # Register
        self.wechat_btn.setStyleSheet("""
            QPushButton {
                background-color: #07C160;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #36D57D;
            }
            QPushButton:pressed {
                background-color: #06AD56;
            }
            QPushButton:checked {
                background-color: #06AD56;
            }
        """)
        self.wechat_btn.setCheckable(True)
        self.wechat_btn.clicked.connect(lambda: self.switch_qr('wechat'))
        button_layout.addWidget(self.wechat_btn)
        
        layout.addWidget(button_container)
        
        # 创建堆叠部件来切换二维码
        self.qr_stack = QStackedWidget()
        layout.addWidget(self.qr_stack)
        
        # 获取资源目录路径
        resources_dir = self.get_resources_path()
        
        # 支付宝二维码页面
        alipay_page = QWidget()
        alipay_layout = QVBoxLayout(alipay_page)
        alipay_qr = QLabel()
        alipay_path = os.path.join(resources_dir, "alipay.png")
        if os.path.exists(alipay_path):
            pixmap = QPixmap(alipay_path)
            if not pixmap.isNull():
                alipay_qr.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                alipay_qr.setText(_("sponsor_qr_load_error")) # Translate
        else:
            alipay_qr.setText(_("sponsor_qr_not_found")) # Translate
        alipay_layout.addWidget(alipay_qr, alignment=Qt.AlignmentFlag.AlignCenter)
        self.qr_stack.addWidget(alipay_page)
        
        # 微信二维码页面
        wechat_page = QWidget()
        wechat_layout = QVBoxLayout(wechat_page)
        wechat_qr = QLabel()
        wechat_path = os.path.join(resources_dir, "wechat.png")
        if os.path.exists(wechat_path):
            pixmap = QPixmap(wechat_path)
            if not pixmap.isNull():
                wechat_qr.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                wechat_qr.setText(_("sponsor_qr_load_error")) # Translate
        else:
            wechat_qr.setText(_("sponsor_qr_not_found")) # Translate
        wechat_layout.addWidget(wechat_qr, alignment=Qt.AlignmentFlag.AlignCenter)
        self.qr_stack.addWidget(wechat_page)
        
        # 默认显示支付宝
        self.qr_stack.setCurrentIndex(0)
    
    def switch_qr(self, qr_type):
        """切换二维码显示"""
        if qr_type == 'alipay':
            self.qr_stack.setCurrentIndex(0)
            self.alipay_btn.setChecked(True)
            self.wechat_btn.setChecked(False)
        else:
            self.qr_stack.setCurrentIndex(1)
            self.alipay_btn.setChecked(False)
            self.wechat_btn.setChecked(True)
    
    def get_resources_path(self):
        """获取资源目录路径"""
        # 尝试多个可能的路径
        possible_paths = [
            # 当前目录下的resources
            os.path.join(os.path.dirname(__file__), '..', 'resources'),
            # 程序运行目录下的resources
            os.path.join(os.getcwd(), 'resources'),
            # 可执行文件目录下的resources
            os.path.join(os.path.dirname(sys.executable), 'resources')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 如果都不存在，创建一个resources目录
        default_path = os.path.join(os.path.dirname(__file__), '..', 'resources')
        os.makedirs(default_path, exist_ok=True)
        return default_path 