#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTabWidget, QWidget, QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class HelpDialog(QDialog):
    """使用说明对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用说明")
        self.setModal(True)
        self.setGeometry(100, 100, 800, 600)
        # 设置最小大小，允许用户调整但不会太小
        self.setMinimumSize(500, 300)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("📚 使用说明 作者@hy499 ")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2196F3; padding: 15px;")
        layout.addWidget(title)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 添加各个说明页面
        self.tab_widget.addTab(self.create_overview_tab(), "📖 功能概述")
        self.tab_widget.addTab(self.create_quick_start_tab(), "🚀 快速开始")
        self.tab_widget.addTab(self.create_account_management_tab(), "👤 账号管理")
        self.tab_widget.addTab(self.create_monitoring_tab(), "📡 监听功能")
        self.tab_widget.addTab(self.create_config_tab(), "⚙️ 配置说明")
        self.tab_widget.addTab(self.create_troubleshooting_tab(), "🔧 故障排除")
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumHeight(40)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
    def create_overview_tab(self):
        """创建功能概述页面"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 功能介绍
        overview_group = QGroupBox("🎯 主要功能")
        overview_layout = QVBoxLayout(overview_group)
        
        features = [
            "📱 多账号管理：支持添加和管理多个 Telegram 账号",
            "🔄 群组克隆：自动监听源群组消息并转发到目标群组",
            "👥 用户克隆：自动克隆用户到目标群组",
            "🖼️ 头像管理：批量清理账号头像",
            "📥 群组加入：自动加入指定的目标群组",
            "⚙️ 灵活配置：支持代理、黑名单、关键词替换等",
            "📊 实时监控：实时显示运行状态和统计信息"
        ]
        
        for feature in features:
            label = QLabel(f"• {feature}")
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 13px; margin: 5px 0;")
            overview_layout.addWidget(label)
            
        layout.addWidget(overview_group)
        
        # 系统要求
        system_group = QGroupBox("💻 系统要求")
        system_layout = QVBoxLayout(system_group)
        
        requirements = [
            "Python 3.7+",
            "PyQt6",
            "Telethon 库",
            "qasync 库",
            "稳定的网络连接",
            "有效的 Telegram API 凭据"
        ]
        
        for req in requirements:
            label = QLabel(f"✓ {req}")
            label.setStyleSheet("font-size: 13px; margin: 3px 0; color: #4CAF50;")
            system_layout.addWidget(label)
            
        layout.addWidget(system_group)
        
        # 注意事项
        notice_group = QGroupBox("⚠️ 重要提醒")
        notice_layout = QVBoxLayout(notice_group)
        
        notices = [
            "请遵守 Telegram 的使用条款和当地法律法规",
            "不要用于恶意目的或骚扰他人",
            "合理使用，避免被限制或封号",
            "定期备份重要的会话文件",
            "使用代理时请确保代理的合法性"
        ]
        
        for notice in notices:
            label = QLabel(f"• {notice}")
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 13px; margin: 5px 0; color: #FF9800;")
            notice_layout.addWidget(label)
            
        layout.addWidget(notice_group)
        layout.addStretch()
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        return scroll
        
    def create_quick_start_tab(self):
        """创建快速开始页面"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 步骤说明
        steps_group = QGroupBox("📋 快速开始步骤")
        steps_layout = QVBoxLayout(steps_group)
        
        steps = [
            ("1️⃣ 配置API信息", "在'配置管理'页面填写你的 Telegram API ID 和 API HASH"),
            ("2️⃣ 添加账号", "点击'新增账号'，输入手机号并完成验证码登录"),
            ("3️⃣ 配置群组", "设置源群组（监听）和目标群组（转发）"),
            ("4️⃣ 开始监听", "点击'开始监听'按钮启动消息监听和转发"),
            ("5️⃣ 监控状态", "在状态面板查看运行情况和统计信息")
        ]
        
        for step_num, step_desc in steps:
            step_label = QLabel(f"{step_num} {step_desc}")
            step_label.setWordWrap(True)
            step_label.setStyleSheet("font-size: 13px; margin: 8px 0; font-weight: bold;")
            steps_layout.addWidget(step_label)
            
        layout.addWidget(steps_group)
        
        # API获取说明
        api_group = QGroupBox("🔑 如何获取 Telegram API 凭据")
        api_layout = QVBoxLayout(api_group)
        
        api_steps = [
            "1. 访问 https://my.telegram.org",
            "2. 使用你的 Telegram 账号登录",
            "3. 点击 'API development tools'",
            "4. 创建一个新的应用",
            "5. 复制 API ID 和 API HASH",
            "6. 在程序中填入这些信息"
        ]
        
        for api_step in api_steps:
            label = QLabel(api_step)
            label.setStyleSheet("font-size: 12px; margin: 3px 0; color: #666;")
            api_layout.addWidget(label)
            
        layout.addWidget(api_group)
        layout.addStretch()
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        return scroll
        
    def create_account_management_tab(self):
        """创建账号管理页面"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 账号添加
        add_group = QGroupBox("➕ 添加新账号")
        add_layout = QVBoxLayout(add_group)
        
        add_desc = [
            "支持手机号或用户名登录",
            "自动处理验证码和2FA密码",
            "登录成功后自动加入目标群组",
            "账号信息保存在 sessions 文件夹中"
        ]
        
        for desc in add_desc:
            label = QLabel(f"• {desc}")
            label.setStyleSheet("font-size: 13px; margin: 5px 0;")
            add_layout.addWidget(label)
            
        layout.addWidget(add_group)
        
        # 账号状态
        status_group = QGroupBox("📊 账号状态说明")
        status_layout = QVBoxLayout(status_group)
        
        status_desc = [
            ("空闲", "账号已登录但未分配任务"),
            ("已分配", "账号正在执行克隆任务"),
            ("[冻结]", "账号被限制，无法执行某些操作"),
            ("[已删除]", "账号已被删除"),
            ("[机器人]", "这是一个机器人账号")
        ]
        
        for status, desc in status_desc:
            status_label = QLabel(f"• {status}: {desc}")
            status_label.setStyleSheet("font-size: 13px; margin: 5px 0;")
            status_layout.addWidget(status_label)
            
        layout.addWidget(status_group)
        
        # 账号操作
        operation_group = QGroupBox("🛠️ 账号操作")
        operation_layout = QVBoxLayout(operation_group)
        
        operations = [
            "🗑️ 清空头像：批量删除所有账号的头像",
            "📥 加入目标群：让所有账号加入指定的目标群组",
            "🔄 刷新状态：更新账号列表和状态信息"
        ]
        
        for operation in operations:
            label = QLabel(operation)
            label.setStyleSheet("font-size: 13px; margin: 5px 0;")
            operation_layout.addWidget(label)
            
        layout.addWidget(operation_group)
        layout.addStretch()
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        return scroll
        
    def create_monitoring_tab(self):
        """创建监听功能页面"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 监听原理
        principle_group = QGroupBox("🔍 监听工作原理")
        principle_layout = QVBoxLayout(principle_group)
        
        principle_desc = [
            "程序会持续监听指定的源群组",
            "当有新消息时，自动选择空闲账号",
            "使用选中的账号将消息转发到目标群组",
            "同时克隆消息的发送者到目标群组",
            "支持文本、图片、文件等多种消息类型"
        ]
        
        for desc in principle_desc:
            label = QLabel(f"• {desc}")
            label.setWordWrap(True)
            label.setStyleSheet("font-size: 13px; margin: 5px 0;")
            principle_layout.addWidget(label)
            
        layout.addWidget(principle_group)
        
        # 监听控制
        control_group = QGroupBox("🎮 监听控制")
        control_layout = QVBoxLayout(control_group)
        
        controls = [
            "🚀 开始监听：启动消息监听和转发功能",
            "⏹️ 停止监听：停止所有监听活动",
            "监听状态会实时显示在状态面板中"
        ]
        
        for control in controls:
            label = QLabel(control)
            label.setStyleSheet("font-size: 13px; margin: 5px 0;")
            control_layout.addWidget(label)
            
        layout.addWidget(control_group)
        
        # 统计信息
        stats_group = QGroupBox("📈 统计信息")
        stats_layout = QVBoxLayout(stats_group)
        
        stats = [
            "克隆账号数量：当前可用的账号总数",
            "已克隆用户：已克隆到目标群组的用户数",
            "消息映射：已处理的消息数量"
        ]
        
        for stat in stats:
            label = QLabel(f"• {stat}")
            label.setStyleSheet("font-size: 13px; margin: 5px 0;")
            stats_layout.addWidget(label)
            
        layout.addWidget(stats_group)
        layout.addStretch()
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        return scroll
        
    def create_config_tab(self):
        """创建配置说明页面"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 基本配置
        basic_group = QGroupBox("🔧 基本配置")
        basic_layout = QVBoxLayout(basic_group)
        
        basic_configs = [
            ("API ID", "你的 Telegram 应用 ID"),
            ("API HASH", "你的 Telegram 应用哈希值"),
            ("源群组", "要监听的群组，多个用逗号分隔"),
            ("目标群组", "消息要转发到的目标群组")
        ]
        
        for config_name, config_desc in basic_configs:
            config_label = QLabel(f"• {config_name}: {config_desc}")
            config_label.setStyleSheet("font-size: 13px; margin: 5px 0;")
            basic_layout.addWidget(config_label)
            
        layout.addWidget(basic_group)
        
        # 代理配置
        proxy_group = QGroupBox("🌐 代理配置")
        proxy_layout = QVBoxLayout(proxy_group)
        
        proxy_configs = [
            ("代理开启", "是否启用代理连接"),
            ("代理主机", "代理服务器地址"),
            ("代理端口", "代理服务器端口"),
            ("代理类型", "支持 socks5 和 http 类型")
        ]
        
        for config_name, config_desc in proxy_configs:
            config_label = QLabel(f"• {config_name}: {config_desc}")
            config_label.setStyleSheet("font-size: 13px; margin: 5px 0;")
            proxy_layout.addWidget(config_label)
            
        layout.addWidget(proxy_group)
        
        # 高级配置
        advanced_group = QGroupBox("⚡ 高级配置")
        advanced_layout = QVBoxLayout(advanced_group)
        
        advanced_configs = [
            ("黑名单用户", "不克隆的用户ID列表，用逗号分隔"),
            ("黑名单关键词", "包含这些关键词的消息将被过滤"),
            ("替换词", "消息转发时的关键词替换规则，格式：原词=新词")
        ]
        
        for config_name, config_desc in advanced_configs:
            config_label = QLabel(f"• {config_name}: {config_desc}")
            config_label.setWordWrap(True)
            config_label.setStyleSheet("font-size: 13px; margin: 5px 0;")
            advanced_layout.addWidget(config_label)
            
        layout.addWidget(advanced_group)
        layout.addStretch()
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        return scroll
        
    def create_troubleshooting_tab(self):
        """创建故障排除页面"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 常见问题
        faq_group = QGroupBox("❓ 常见问题")
        faq_layout = QVBoxLayout(faq_group)
        
        faqs = [
            ("Q: 程序启动失败怎么办？", "A: 检查 Python 版本、依赖库是否正确安装"),
            ("Q: 无法登录账号？", "A: 确认 API ID/HASH 正确，检查网络连接"),
            ("Q: 账号显示[冻结]状态？", "A: 账号被限制，需要等待解封或联系客服"),
            ("Q: 监听没有效果？", "A: 检查源群组和目标群组配置，确认账号权限"),
            ("Q: 程序运行缓慢？", "A: 检查网络连接，考虑使用代理")
        ]
        
        for question, answer in faqs:
            q_label = QLabel(question)
            q_label.setStyleSheet("font-size: 13px; margin: 8px 0 3px 0; font-weight: bold; color: #2196F3;")
            faq_layout.addWidget(q_label)
            
            a_label = QLabel(answer)
            a_label.setStyleSheet("font-size: 12px; margin: 0 0 8px 20px; color: #666;")
            faq_layout.addWidget(a_label)
            
        layout.addWidget(faq_group)
        
        # 错误代码
        error_group = QGroupBox("🚨 常见错误代码")
        error_layout = QVBoxLayout(error_group)
        
        errors = [
            ("420 FROZEN_METHOD_INVALID", "账号被冻结，无法执行操作"),
            ("401 UNAUTHORIZED", "API 凭据无效或过期"),
            ("400 BAD_REQUEST", "请求参数错误"),
            ("429 TOO_MANY_REQUESTS", "请求过于频繁，需要等待"),
            ("500 INTERNAL_SERVER_ERROR", "服务器内部错误")
        ]
        
        for error_code, error_desc in errors:
            error_label = QLabel(f"• {error_code}: {error_desc}")
            error_label.setStyleSheet("font-size: 12px; margin: 5px 0; color: #F44336;")
            error_layout.addWidget(error_label)
            
        layout.addWidget(error_group)
        
        # 解决建议
        solution_group = QGroupBox("💡 解决建议")
        solution_layout = QVBoxLayout(solution_group)
        
        solutions = [
            "重启程序：关闭程序重新启动",
            "检查配置：确认所有配置项正确",
            "网络检查：测试网络连接是否正常",
            "账号状态：检查账号是否被限制",
            "更新程序：使用最新版本的程序"
        ]
        
        for solution in solutions:
            label = QLabel(f"• {solution}")
            label.setStyleSheet("font-size: 13px; margin: 5px 0; color: #4CAF50;")
            solution_layout.addWidget(label)
            
        layout.addWidget(solution_group)
        layout.addStretch()
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        return scroll

def show_help(parent=None):
    """显示帮助对话框的便捷函数"""
    dialog = HelpDialog(parent)
    dialog.exec()

if __name__ == "__main__":
    # 测试代码
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = HelpDialog()
    dialog.show()
    sys.exit(app.exec())
