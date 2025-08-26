#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import asyncio
import configparser
import logging
from typing import Optional, List

from PyQt6.QtWidgets import (
    QApplication, QDialog, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QTextEdit, QLineEdit, QCheckBox,
    QGroupBox, QGridLayout, QListWidget, QScrollArea, QMessageBox, QFileDialog,
    QFrame, QSplitter, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from qasync import QEventLoop

# 你的模块（请确保存在且接口一致）
from core import (
    Config, load_config, load_existing_sessions, start_monitor,
    clients_pool, cloned_users, message_id_mapping, check_and_join_target
)

# 导入使用说明模块
from help_module import show_help

# logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] - %(levelname)s - %(message)s')

# -------------------------
# 日志 UI Handler（模块级）
# -------------------------
import logging as _logging
class UILogHandler(_logging.Handler):
    def __init__(self, text_widget=None):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        try:
            msg = self.format(record)
            if self.text_widget:
                # append in Qt main thread (qasync runs in main loop)
                self.text_widget.append(msg)
                self.text_widget.verticalScrollBar().setValue(self.text_widget.verticalScrollBar().maximum())
        except Exception:
            pass

# -------------------------
# Login dialog (async)
# -------------------------
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加新账号 - 登录")
        self.setModal(True)
        self.setFixedSize(420, 320)

        self.phone = ""
        self.code = ""
        self.password = ""
        self._phone_code_hash = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("添加新账号")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        phone_layout = QHBoxLayout()
        phone_layout.addWidget(QLabel("手机号:"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+86 13800138000")
        phone_layout.addWidget(self.phone_input)
        layout.addLayout(phone_layout)

        send_layout = QHBoxLayout()
        self.send_code_btn = QPushButton("发送验证码")
        self.send_code_btn.clicked.connect(self._on_send_code_clicked)
        send_layout.addWidget(self.send_code_btn)
        self.sent_info_label = QLabel("")
        send_layout.addWidget(self.sent_info_label)
        send_layout.addStretch()
        layout.addLayout(send_layout)

        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("验证码:"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("收到的短信/Telegram 验证码")
        code_layout.addWidget(self.code_input)
        layout.addLayout(code_layout)

        pass_layout = QHBoxLayout()
        pass_layout.addWidget(QLabel("2FA 密码:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("可选，若帐户启用 2FA 则填写")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        pass_layout.addWidget(self.password_input)
        layout.addLayout(pass_layout)

        note = QLabel("说明：点击“发送验证码”会使用你在配置中的 API ID/HASH 发送请求。")
        note.setWordWrap(True)
        note.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(note)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self._on_accept_clicked)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def _on_send_code_clicked(self):
        phone = self.phone_input.text().strip()
        if not phone:
            QMessageBox.warning(self, "警告", "请输入手机号或用户名")
            return
        # schedule async task on main loop
        self.send_code_btn.setEnabled(False)
        self.sent_info_label.setText("发送中...")
        asyncio.create_task(self._async_send_code(phone))

    async def _async_send_code(self, phone: str):
        from telethon import TelegramClient
        try:
            api_id = getattr(Config, "API_ID", None)
            api_hash = getattr(Config, "API_HASH", None)
            proxy = getattr(Config, "PROXY", None) if hasattr(Config, "PROXY") else None
            if not api_id or not api_hash:
                raise RuntimeError("Config.API_ID / API_HASH 未设置，请先在配置中填写并重新加载。")

            session_name = f"{phone}"
            # 使用 async client
            client = TelegramClient(session_name, api_id, api_hash, proxy=proxy)
            await client.connect()
            res = await client.send_code_request(phone)
            phone_code_hash = getattr(res, "phone_code_hash", None)
            await client.disconnect()

            if not phone_code_hash:
                self.sent_info_label.setText("发送失败（未返回 phone_code_hash）")
            else:
                self._phone_code_hash = phone_code_hash
                self.sent_info_label.setText("验证码已发送，请查看短信或 Telegram")
                logging.info("send_code_request succeeded; phone_code_hash saved.")
        except Exception as e:
            self.sent_info_label.setText("发送失败")
            logging.exception("send_code_request error")
            QMessageBox.critical(self, "发送验证码失败", str(e))
        finally:
            self.send_code_btn.setEnabled(True)

    def _on_accept_clicked(self):
        phone = self.phone_input.text().strip()
        code = self.code_input.text().strip()
        password = self.password_input.text().strip()
        if not phone:
            QMessageBox.warning(self, "警告", "请输入手机号或用户名")
            return
        if not code:
            QMessageBox.warning(self, "警告", "请输入验证码")
            return
        self.phone = phone
        self.code = code
        self.password = password
        super().accept()

    def get_phone_code_hash(self) -> Optional[str]:
        return self._phone_code_hash

# -------------------------
# 主窗口
# -------------------------
class ModernUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telegram Group Cloner 作者@hy499")
        self.setGeometry(100, 100, 800, 500)

        self.primary_color = "#2196F3"
        self.success_color = "#4CAF50"
        self.danger_color = "#F44336"
        self.secondary_color = "#FF9800"

        self.is_monitoring = False
        self.async_tasks: List[asyncio.Task] = []  # 保存由 asyncio.create_task 创建的任务引用，防止被 GC

        self.config_entries = {}
        self._setup_ui()

        # 初次加载 config（不重复记录 UI handler）
        try:
            load_config()
            self.load_config_to_ui()
        except Exception as e:
            logging.error(f"初次加载配置失败: {e}")

        # 日志重定向（只添加一次）
        self.setup_log_redirect()

        # 状态定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(3000)
        
        # 启动时加载现有 sessions（延迟执行，等待事件循环启动）
        QTimer.singleShot(1000, self._schedule_load_sessions)
        
        # 启动任务工作器
        QTimer.singleShot(500, self._start_task_worker)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        title = QLabel("Telegram Group Cloner 作者@hy499")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.primary_color}; padding: 10px 0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        hor_split = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(hor_split, stretch=10)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(8,8,8,8)

        nav_label = QLabel("导航")
        nav_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(nav_label)

        self.nav_main_btn = QPushButton("主操作")
        self.nav_main_btn.clicked.connect(lambda: self.switch_page(0))
        self.nav_main_btn.setMinimumHeight(44)
        left_layout.addWidget(self.nav_main_btn)

        self.nav_config_btn = QPushButton("配置管理")
        self.nav_config_btn.clicked.connect(lambda: self.switch_page(1))
        self.nav_config_btn.setMinimumHeight(44)
        left_layout.addWidget(self.nav_config_btn)

        # 添加帮助按钮
        self.nav_help_btn = QPushButton("❓ 使用说明")
        self.nav_help_btn.clicked.connect(self.show_help_dialog)
        self.nav_help_btn.setMinimumHeight(44)
        self.nav_help_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        left_layout.addWidget(self.nav_help_btn)

        left_layout.addStretch()

        left_layout.addWidget(QLabel("已登录账号"))
        self.left_account_list = QListWidget()
        self.left_account_list.setMinimumWidth(220)
        left_layout.addWidget(self.left_account_list)

        hor_split.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8,8,8,8)

        self.pages = QStackedWidget()
        right_layout.addWidget(self.pages)

        page_main = QWidget()
        self._setup_main_tab(page_main)
        self.pages.addWidget(page_main)

        page_config = QWidget()
        self._setup_config_tab(page_config)
        self.pages.addWidget(page_config)

        hor_split.addWidget(right_widget)
        hor_split.setStretchFactor(0, 0)
        hor_split.setStretchFactor(1, 1)

        # 底部日志
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(160)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("background-color: #111; color: #eee; padding: 8px; border-radius: 4px;")
        main_layout.addWidget(self.log_text, stretch=0)

        self.statusBar().showMessage("就绪")
        self.switch_page(0)

    def _setup_main_tab(self, parent):
        layout = QVBoxLayout(parent)
        button_group = QGroupBox("快速操作")
        bl = QVBoxLayout(button_group)

        row1 = QHBoxLayout()
        self.add_account_btn = QPushButton("➕ 新增账号")
        self.add_account_btn.clicked.connect(self.add_new_account)
        self.add_account_btn.setMinimumHeight(44)
        row1.addWidget(self.add_account_btn)

        self.start_monitor_btn = QPushButton("🚀 开始监听")
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        self.start_monitor_btn.setMinimumHeight(44)
        row1.addWidget(self.start_monitor_btn)

        self.stop_monitor_btn = QPushButton("⏹️ 停止监听")
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitor_btn.setMinimumHeight(44)
        self.stop_monitor_btn.setEnabled(False)
        row1.addWidget(self.stop_monitor_btn)

        bl.addLayout(row1)

        row2 = QHBoxLayout()
        self.clear_photos_btn = QPushButton("🗑️ 清空头像")
        self.clear_photos_btn.clicked.connect(self.clear_profile_photos)
        self.clear_photos_btn.setMinimumHeight(44)
        row2.addWidget(self.clear_photos_btn)

        self.join_target_btn = QPushButton("📥 加入目标群")
        self.join_target_btn.clicked.connect(self.join_target_group)
        self.join_target_btn.setMinimumHeight(44)
        row2.addWidget(self.join_target_btn)

        self.refresh_status_btn = QPushButton("🔄 刷新状态")
        self.refresh_status_btn.clicked.connect(self.refresh_status)
        self.refresh_status_btn.setMinimumHeight(44)
        row2.addWidget(self.refresh_status_btn)
        bl.addLayout(row2)
        layout.addWidget(button_group)

        status_group = QGroupBox("运行状态")
        sl = QHBoxLayout(status_group)

        left_sl = QVBoxLayout()
        self.status_labels = {}
        items = [
            ("监听状态", "未开始"),
            ("克隆账号数量", "0"),
            ("已克隆用户", "0"),
            ("消息映射", "0")
        ]
        for key, val in items:
            h = QHBoxLayout()
            lbl = QLabel(f"{key}:")
            lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            h.addWidget(lbl)
            v = QLabel(val)
            h.addWidget(v)
            self.status_labels[key] = v
            left_sl.addLayout(h)
        sl.addLayout(left_sl)

        right_sl = QVBoxLayout()
        right_sl.addWidget(QLabel("克隆账号列表"))
        self.account_listbox = QListWidget()
        self.account_listbox.setMinimumHeight(140)
        right_sl.addWidget(self.account_listbox)
        sl.addLayout(right_sl)

        layout.addWidget(status_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _setup_config_tab(self, parent):
        layout = QVBoxLayout(parent)
        scroll = QScrollArea()
        sw = QWidget()
        sl = QGridLayout(sw)
        sl.setContentsMargins(8,8,8,8)

        sl.addWidget(QLabel("API ID:"), 0, 0)
        self.config_entries['api_id'] = QLineEdit()
        sl.addWidget(self.config_entries['api_id'], 0, 1)

        sl.addWidget(QLabel("API HASH:"), 1, 0)
        self.config_entries['api_hash'] = QLineEdit()
        sl.addWidget(self.config_entries['api_hash'], 1, 1)

        sl.addWidget(QLabel("源群组（逗号分隔）:"), 2, 0)
        self.config_entries['source_group'] = QLineEdit()
        sl.addWidget(self.config_entries['source_group'], 2, 1)

        sl.addWidget(QLabel("目标群组:"), 3, 0)
        self.config_entries['target_group'] = QLineEdit()
        sl.addWidget(self.config_entries['target_group'], 3, 1)

        sl.addWidget(QLabel("代理开启:"), 4, 0)
        self.config_entries['proxy_enabled'] = QCheckBox()
        sl.addWidget(self.config_entries['proxy_enabled'], 4, 1)
        sl.addWidget(QLabel("代理 host:"), 5, 0)
        self.config_entries['proxy_host'] = QLineEdit()
        sl.addWidget(self.config_entries['proxy_host'], 5, 1)
        sl.addWidget(QLabel("代理 port:"), 6, 0)
        self.config_entries['proxy_port'] = QLineEdit()
        sl.addWidget(self.config_entries['proxy_port'], 6, 1)
        sl.addWidget(QLabel("代理类型（socks5/http）:"), 7, 0)
        self.config_entries['proxy_type'] = QLineEdit()
        sl.addWidget(self.config_entries['proxy_type'], 7, 1)

        sl.addWidget(QLabel("黑名单用户 IDs（逗号）:"), 8, 0)
        self.config_entries['blacklist_user_ids'] = QLineEdit()
        sl.addWidget(self.config_entries['blacklist_user_ids'], 8, 1)
        sl.addWidget(QLabel("黑名单关键词（逗号）:"), 9, 0)
        self.config_entries['blacklist_keywords'] = QLineEdit()
        sl.addWidget(self.config_entries['blacklist_keywords'], 9, 1)

        sl.addWidget(QLabel("替换词（k=v,逗号分隔）:"), 10, 0)
        self.config_entries['replacements'] = QLineEdit()
        sl.addWidget(self.config_entries['replacements'], 10, 1)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 保存配置")
        save_btn.clicked.connect(self.save_config)
        btn_row.addWidget(save_btn)
        reload_btn = QPushButton("🔄 重新加载")
        reload_btn.clicked.connect(self.reload_config)
        btn_row.addWidget(reload_btn)
        btn_row.addStretch()
        sl.addLayout(btn_row, 11, 0, 1, 2)

        scroll.setWidget(sw)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

    def switch_page(self, index:int):
        self.pages.setCurrentIndex(index)
        self.nav_main_btn.setStyleSheet("" if index!=0 else f"background-color:{self.primary_color}; color:white;")
        self.nav_config_btn.setStyleSheet("" if index!=1 else f"background-color:{self.primary_color}; color:white;")
    
    def show_help_dialog(self):
        """显示使用说明对话框"""
        try:
            show_help(self)
        except Exception as e:
            logging.error(f"显示帮助对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"无法显示使用说明: {e}")

    # -------------------------
    # 日志重定向（只添加一次 handler）
    # -------------------------
    def setup_log_redirect(self):
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        have = False
        for h in root_logger.handlers:
            if isinstance(h, UILogHandler):
                h.text_widget = self.log_text
                have = True
                break
        if not have:
            ui_handler = UILogHandler(self.log_text)
            ui_handler.setFormatter(logging.Formatter('[%(asctime)s] - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
            root_logger.addHandler(ui_handler)

    # -------------------------
    # 配置加载 / 保存
    # -------------------------
    def load_config_to_ui(self):
        try:
            if hasattr(Config, 'API_ID'):
                self.config_entries['api_id'].setText(str(getattr(Config, 'API_ID', '') or ''))
            if hasattr(Config, 'API_HASH'):
                self.config_entries['api_hash'].setText(getattr(Config, 'API_HASH', '') or '')
            if hasattr(Config, 'SOURCE_GROUPS'):
                self.config_entries['source_group'].setText(','.join(getattr(Config, 'SOURCE_GROUPS', [])) or '')
            if hasattr(Config, 'TARGET_GROUP'):
                self.config_entries['target_group'].setText(str(getattr(Config, 'TARGET_GROUP', '') or ''))
            proxy = getattr(Config, 'PROXY', None)
            if proxy and isinstance(proxy, (list, tuple)):
                try:
                    host = proxy[0][0] if isinstance(proxy[0], (list, tuple)) else ''
                    self.config_entries['proxy_host'].setText(host or '')
                except Exception:
                    pass
            self.update_status()
        except Exception as e:
            logging.error(f"load_config_to_ui error: {e}")

    def save_config(self):
        try:
            config = configparser.ConfigParser()
            path = "setting/config.ini"
            if os.path.exists(path):
                config.read(path, encoding="utf-8-sig")
            if not config.has_section("telegram"):
                config.add_section("telegram")
            config.set("telegram", "api_id", self.config_entries['api_id'].text())
            config.set("telegram", "api_hash", self.config_entries['api_hash'].text())
            config.set("telegram", "source_group", self.config_entries['source_group'].text())
            config.set("telegram", "target_group", self.config_entries['target_group'].text())

            if not config.has_section("proxy"):
                config.add_section("proxy")
            config.set("proxy", "is_enabled", str(self.config_entries['proxy_enabled'].isChecked()).lower())
            config.set("proxy", "host", self.config_entries['proxy_host'].text())
            config.set("proxy", "port", self.config_entries['proxy_port'].text())
            config.set("proxy", "type", self.config_entries['proxy_type'].text())

            if not config.has_section("blacklist"):
                config.add_section("blacklist")
            config.set("blacklist", "user_ids", self.config_entries['blacklist_user_ids'].text())
            config.set("blacklist", "keywords", self.config_entries['blacklist_keywords'].text())

            if not config.has_section("replacements"):
                config.add_section("replacements")
            rep_text = self.config_entries['replacements'].text().strip()
            if config.has_section("replacements"):
                for k in list(config["replacements"]):
                    config.remove_option("replacements", k)
            if rep_text:
                for item in rep_text.split(','):
                    if '=' in item:
                        k, v = item.split('=', 1)
                        config.set("replacements", k.strip(), v.strip())

            os.makedirs("setting", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                config.write(f)
            QMessageBox.information(self, "成功", "配置已保存")
            self.reload_config()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")

    def reload_config(self):
        try:
            load_config()
            self.load_config_to_ui()
            #logging.info("成功加载配置文件: setting/config.ini")
            QMessageBox.information(self, "成功", "配置已重新加载")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重新加载配置失败: {e}")

    # -------------------------
    # 状态更新
    # -------------------------
    def update_status(self):
        try:
            self.status_labels["克隆账号数量"].setText(str(len(clients_pool)))
            self.status_labels["已克隆用户"].setText(str(len(cloned_users)))
            self.status_labels["消息映射"].setText(str(len(message_id_mapping)))
            self.account_listbox.clear()
            self.left_account_list.clear()
            
            # 异步更新账号列表（检查事件循环状态）
            self._schedule_update_accounts()
        except Exception as e:
            logging.error(f"更新状态失败: {e}")
    
    def _schedule_load_sessions(self):
        """调度加载 sessions 任务"""
        try:
            # 使用更现代的方式检查事件循环
            try:
                loop = asyncio.get_running_loop()
                # 如果成功获取到运行中的事件循环，创建任务
                asyncio.create_task(self._load_existing_sessions())
            except RuntimeError:
                # 如果没有运行中的事件循环，延迟执行
                QTimer.singleShot(500, self._schedule_load_sessions)
        except Exception:
            # 如果获取事件循环失败，再次延迟
            QTimer.singleShot(500, self._schedule_load_sessions)
    
    def _schedule_update_accounts(self):
        """调度更新账号列表任务"""
        try:
            # 使用更现代的方式检查事件循环
            try:
                loop = asyncio.get_running_loop()
                # 如果成功获取到运行中的事件循环，直接创建任务
                asyncio.create_task(self._update_account_lists())
            except RuntimeError:
                # 如果没有运行中的事件循环，延迟执行
                QTimer.singleShot(100, self._schedule_update_accounts)
        except Exception:
            # 如果获取事件循环失败，延迟执行
            QTimer.singleShot(100, self._schedule_update_accounts)
    
    def _start_task_worker(self):
        """启动任务工作器（简化版）"""
        try:
            try:
                loop = asyncio.get_running_loop()
                # 如果成功获取到运行中的事件循环，记录日志
                logging.info("事件循环已启动，任务工作器就绪")
            except RuntimeError:
                # 如果没有运行中的事件循环，延迟执行
                QTimer.singleShot(500, self._start_task_worker)
        except Exception:
            # 如果获取事件循环失败，延迟执行
            QTimer.singleShot(500, self._start_task_worker)
    
    async def _load_existing_sessions(self):
        """程序启动时加载现有的 sessions"""
        try:
            logging.info("正在加载现有的 sessions...")
            # 检查是否已经有 clients 在运行
            if not clients_pool:
                try:
                    # 添加超时保护，避免长时间卡住
                    await asyncio.wait_for(load_existing_sessions('2'), timeout=30.0)
                    logging.info("现有 sessions 加载完成")
                except asyncio.TimeoutError:
                    logging.warning("加载 sessions 超时，可能网络较慢")
                except KeyboardInterrupt:
                    logging.info("用户中断了 sessions 加载")
                except Exception as e:
                    logging.error(f"加载 sessions 时发生错误: {e}")
            else:
                logging.info("已有 clients 在运行，跳过重复加载")
            # 加载完成后立即更新状态
            self.update_status()
        except Exception as e:
            logging.error(f"加载现有 sessions 失败: {e}")
    
    async def _update_account_lists(self):
        """异步更新账号列表，获取真实的手机号"""
        try:
            for client, cloned_user in list(clients_pool.items()):
                try:
                    # 使用 get_me() 获取真实的用户信息
                    me = await client.get_me()
                    phone = me.phone if me and me.phone else "未知手机号"
                    status = "已分配" if cloned_user else "空闲"
                    
                    # 检查账号是否被限制/冻结
                    account_status = ""
                    if me and hasattr(me, 'restricted') and me.restricted:
                        account_status = " [冻结]"
                    elif me and hasattr(me, 'deleted') and me.deleted:
                        account_status = " [已删除]"
                    elif me and hasattr(me, 'bot') and me.bot:
                        account_status = " [机器人]"
                    
                    item_text = f"{phone} - {status}{account_status}"
                except Exception as e:
                    # 如果获取失败，尝试从 session 文件名获取
                    try:
                        session_path = getattr(client, 'session', None)
                        if session_path:
                            if hasattr(session_path, 'filename'):
                                filename = os.path.basename(session_path.filename)
                            else:
                                filename = str(session_path)
                            phone = filename.replace('.session', '') if filename.endswith('.session') else filename
                        else:
                            phone = "未知账号"
                    except:
                        phone = "未知账号"
                    status = "已分配" if cloned_user else "空闲"
                    item_text = f"{phone} - {status} [状态未知]"
                
                # 在主线程中更新 UI
                self.account_listbox.addItem(item_text)
                self.left_account_list.addItem(item_text)
        except Exception as e:
            logging.error(f"更新账号列表失败: {e}")

    # -------------------------
    # 新增账号（async flow）
    # -------------------------
    def add_new_account(self):
        dlg = LoginDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        phone = dlg.phone
        code = dlg.code
        password = dlg.password
        phone_code_hash = dlg.get_phone_code_hash()
        # 直接创建登录任务
        asyncio.create_task(self._do_login(phone, code, password, phone_code_hash))
        # UI feedback
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

    async def _do_login(self, phone, code, password, phone_code_hash):
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError
        try:
            api_id = getattr(Config, "API_ID", None)
            api_hash = getattr(Config, "API_HASH", None)
            proxy = getattr(Config, "PROXY", None) if hasattr(Config, "PROXY") else None
            if not api_id or not api_hash:
                raise RuntimeError("Config.API_ID / API_HASH 未配置。")

            session_path = f"sessions/{phone}"
            client = TelegramClient(session_path, api_id, api_hash, proxy=proxy)
            await client.connect()
            try:
                if not await client.is_user_authorized():
                    if phone_code_hash:
                        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
                    else:
                        y = await client.send_code_request(phone)
                        await client.sign_in(phone=phone, code=code, phone_code_hash=y.phone_code_hash)
            except SessionPasswordNeededError:
                if password:
                    await client.sign_in(password=password)
                else:
                    await client.disconnect()
                    raise RuntimeError("需要 2FA 密码，但未提供。")
            try:
                await check_and_join_target(client)
            except Exception as e:
                logging.warning(f"加入目标群时发生错误（可忽略）：{e}")
            clients_pool[client] = None
            logging.info(f"账号 {phone} 添加成功")
            # UI updates
            self.on_operation_complete(f"账号 {phone} 添加成功")
        except Exception as e:
            logging.exception("添加账号失败")
            self.on_operation_error(f"添加账号失败: {e}")
        finally:
            self.progress_bar.setVisible(False)

    # -------------------------
    # 监听 / 停止（async）
    # -------------------------
    def start_monitoring(self):
        if self.is_monitoring:
            return
        # 直接创建监听任务
        asyncio.create_task(self._start_monitor_wrapper())
        self.is_monitoring = True
        self.start_monitor_btn.setEnabled(False)
        self.stop_monitor_btn.setEnabled(True)
        self.status_labels["监听状态"].setText("正在监听")
        self.statusBar().showMessage("正在监听消息...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

    async def _start_monitor_wrapper(self):
        try:
            # 不再重复加载 sessions，因为启动时已经加载过了
            # await load_existing_sessions('2')
            try:
                # 添加超时保护
                await asyncio.wait_for(start_monitor(), timeout=60.0)
            except asyncio.TimeoutError:
                logging.warning("监听启动超时，可能网络较慢")
                self.on_operation_error("监听启动超时，请检查网络连接")
            except KeyboardInterrupt:
                logging.info("用户中断了监听")
                self.on_operation_error("监听被用户中断")
        except Exception as e:
            logging.exception("监听失败")
            self.on_operation_error(f"监听失败: {e}")
        finally:
            logging.info("监听任务结束")
            self.progress_bar.setVisible(False)

    def stop_monitoring(self):
        # 安全地停止监听
        if self.is_monitoring:
            self.is_monitoring = False
            
        self.start_monitor_btn.setEnabled(True)
        self.stop_monitor_btn.setEnabled(False)
        self.status_labels["监听状态"].setText("已停止")
        self.statusBar().showMessage("监听已停止")
        self.progress_bar.setVisible(False)

    # -------------------------
    # 其他异步操作（清空头像 / 加入目标群）
    # -------------------------
    def clear_profile_photos(self):
        # 直接创建头像清理任务
        asyncio.create_task(self._run_load_existing('3'))
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

    def join_target_group(self):
        # 直接创建加入目标群任务
        asyncio.create_task(self._run_load_existing('4'))
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

    async def _run_load_existing(self, flag):
        try:
            # 检查是否已经有连接的客户端
            if clients_pool:
                logging.info("已有连接的客户端，跳过重复加载")
                if flag == '3':
                    # 对现有客户端执行头像清理
                    for client in list(clients_pool.keys()):
                        try:
                            # 先检查账号状态
                            me = await client.get_me()
                            if me and hasattr(me, 'restricted') and me.restricted:
                                logging.warning(f"账号 {me.phone or '未知'} 被限制，跳过头像清理")
                                continue
                            
                            from core import delete_profile_photos
                            await delete_profile_photos(client)
                        except Exception as e:
                            if "FROZEN_METHOD_INVALID" in str(e) or "420" in str(e):
                                logging.warning(f"账号被冻结，无法执行头像清理操作")
                            else:
                                logging.warning(f"清理头像失败: {e}")
                    self.on_operation_complete("头像清理完成")
                else:
                    # 对现有客户端执行加入目标群
                    for client in list(clients_pool.keys()):
                        try:
                            # 先检查账号状态
                            me = await client.get_me()
                            if me and hasattr(me, 'restricted') and me.restricted:
                                logging.warning(f"账号 {me.phone or '未知'} 被限制，跳过加入目标群")
                                continue
                            
                            from core import check_and_join_target
                            await check_and_join_target(client)
                        except Exception as e:
                            if "FROZEN_METHOD_INVALID" in str(e) or "420" in str(e):
                                logging.warning(f"账号被冻结，无法执行加入目标群操作")
                            else:
                                logging.warning(f"加入目标群失败: {e}")
                    self.on_operation_complete("加入目标群完成")
            else:
                # 如果没有连接的客户端，才加载 sessions
                try:
                    # 添加超时保护
                    await asyncio.wait_for(load_existing_sessions(flag), timeout=30.0)
                    if flag == '3':
                        self.on_operation_complete("头像清理完成")
                    else:
                        self.on_operation_complete("加入目标群完成")
                except asyncio.TimeoutError:
                    logging.warning("操作超时，可能网络较慢")
                    self.on_operation_error("操作超时，请检查网络连接")
                except KeyboardInterrupt:
                    logging.info("用户中断了操作")
                    self.on_operation_error("操作被用户中断")
                except Exception as e:
                    logging.error(f"执行操作时发生错误: {e}")
                    self.on_operation_error(f"操作失败: {e}")
        except Exception as e:
            logging.exception("操作失败")
            self.on_operation_error(f"操作失败: {e}")
        finally:
            self.progress_bar.setVisible(False)

    def refresh_status(self):
        self.update_status()
        QMessageBox.information(self, "成功", "状态已刷新")

    # -------------------------
    # 日志保存 / 清空
    # -------------------------
    def clear_log(self):
        self.log_text.clear()

    def save_log(self):
        fname, _ = QFileDialog.getSaveFileName(self, "保存日志", "", "文本文件 (*.txt);;所有文件 (*.*)")
        if not fname:
            return
        try:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(self.log_text.toPlainText())
            QMessageBox.information(self, "成功", f"日志已保存到: {fname}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存日志失败: {e}")

    # -------------------------
    # 回调
    # -------------------------
    def on_operation_complete(self, message):
        self.update_status()
        self.progress_bar.setVisible(False)
        try:
            QMessageBox.information(self, "成功", message)
        except Exception:
            logging.info(message)

    def on_operation_error(self, message):
        self.progress_bar.setVisible(False)
        try:
            QMessageBox.critical(self, "错误", message)
        except Exception:
            logging.error(message)

    # -------------------------
    # 退出时尝试异步清理（调度一个 cleanup task）
    # -------------------------
    def closeEvent(self, event):
        logging.info("程序正在退出：调度清理任务...")
        try:
            # schedule cleanup task but don't block the UI here
            asyncio.create_task(self._async_cleanup())
        except Exception:
            pass
        event.accept()

    async def _async_cleanup(self):
        logging.info("开始异步清理：取消未完成任务与断开 clients")
        # cancel outstanding tasks (except current)
        try:
            current = asyncio.current_task()
            tasks = [t for t in asyncio.all_tasks() if t is not current]
            for t in tasks:
                try:
                    t.cancel()
                except Exception:
                    pass
            # give them a small moment to cancel
            await asyncio.sleep(0.1)
        except Exception:
            pass

        # disconnect clients in clients_pool
        for client in list(clients_pool.keys()):
            try:
                coro = getattr(client, "disconnect", None)
                if coro:
                    res = coro()
                    if asyncio.iscoroutine(res):
                        try:
                            await res
                        except Exception:
                            pass
            except Exception:
                pass
        logging.info("异步清理完成。")

# -------------------------
# main
# -------------------------
def main():
    try:
        os.makedirs("setting", exist_ok=True)
        os.makedirs("sessions", exist_ok=True)

        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        window = ModernUI()
        window.show()

        # run event loop
        with loop:
            loop.run_forever()

    except Exception as e:
        print(f"程序启动失败: {e}")

if __name__ == "__main__":
    main()