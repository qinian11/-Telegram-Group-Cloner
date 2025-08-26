# Telegram Group Cloner 增强版

## 新增功能

## 🚀 功能特性

- **📱 多账号管理**: 支持添加和管理多个 Telegram 账号
- **🔄 群组克隆**: 自动监听源群组消息并转发到目标群组
- **👥 用户克隆**: 自动克隆用户到目标群组
- **🖼️ 头像管理**: 批量清理账号头像
- **📥 群组加入**: 自动加入指定的目标群组
- **⚙️ 灵活配置**: 支持代理、黑名单、关键词替换等
- **📊 实时监控**: 实时显示运行状态和统计信息
- **🎨 现代化UI**: 基于 PyQt6 的图形用户界面

## 📋 系统要求

#### 3. 自动监听保护
- **实时保护**: 监听过程中持续监控账号状态
- **自动停止**: 当所有账号失效时自动停止监听
- **用户通知**: 及时通知用户账号状态变化

## 🛠️ 安装说明

### 1. 克隆项目
```bash
git clone <repository-url>
cd telegram-group-cloner
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置设置
编辑 `setting/config.ini` 文件：
```ini
[telegram]
api_id = YOUR_API_ID
api_hash = YOUR_API_HASH
source_group = SOURCE_GROUP_LINK
target_group = TARGET_GROUP_LINK

[proxy]
is_enabled = false
host = 
port = 
type = 

[blacklist]
user_ids = 
keywords = 

[replacements]
```

## 🔑 获取 Telegram API 凭据

1. 访问 [my.telegram.org](https://my.telegram.org)
2. 登录你的 Telegram 账号
3. 创建一个新的应用
4. 复制 `api_id` 和 `api_hash`

## 🚀 使用方法

### 启动应用
```bash
python tg_group_cloner_ui.py
```

### 主要功能

#### 1. 账号管理
- 点击"添加新账号"按钮
- 输入手机号或用户名
- 发送验证码并完成登录
- 管理已登录的账号

#### 2. 群组克隆
- 设置源群组和目标群组
- 启动监听功能
- 自动转发消息和克隆用户

#### 3. 头像管理
- 批量清理账号头像
- 支持选择性清理

#### 4. 群组加入
- 自动加入指定的目标群组
- 批量操作支持

## 📁 项目结构

```
telegram-group-cloner/
├── main.py      # 主界面程序
├── core.py         # 核心功能模块
├── help_module.py             # 帮助说明模块
├── setting/
│   └── config.ini            # 配置文件
├── sessions/                  # 会话文件存储
├── monitor.session           # 监控会话
└── app.log                   # 应用日志
```

## ⚙️ 配置选项

### Telegram 配置
- `api_id`: Telegram API ID
- `api_hash`: Telegram API Hash
- `source_group`: 源群组链接
- `target_group`: 目标群组链接

### 代理配置
- `is_enabled`: 是否启用代理
- `host`: 代理服务器地址
- `port`: 代理服务器端口
- `type`: 代理类型

### 黑名单配置
- `user_ids`: 用户ID黑名单
- `keywords`: 关键词黑名单

### 替换配置
- 支持消息内容替换规则

## 🔧 故障排除

### 常见问题

1. **登录失败**
   - 检查网络连接
   - 验证 API 凭据
   - 确认手机号格式

2. **消息转发失败**
   - 检查群组权限
   - 验证账号状态
   - 查看日志信息

3. **代理连接问题**
   - 检查代理服务器状态
   - 验证代理配置
   - 测试网络连通性

### 日志查看
应用运行时会生成 `app.log` 文件，包含详细的运行信息和错误日志。

## 📚 使用说明

应用内置了详细的使用说明，点击界面中的"帮助"按钮即可查看：
- 功能概述
- 快速开始指南
- 账号管理说明
- 监听功能介绍
- 配置说明
- 故障排除指南

## ⚠️ 注意事项

1. **合规使用**: 请确保遵守 Telegram 服务条款和当地法律法规
2. **账号安全**: 不要在不信任的环境中使用你的 Telegram 账号
3. **频率限制**: 避免过于频繁的操作，以免触发限制
4. **数据备份**: 定期备份重要的会话文件和配置

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 📄 许可证

本项目仅供学习和研究使用，请勿用于商业用途。

## 📞 支持

如果你遇到问题或需要帮助，请：
1. 查看应用内置的帮助文档
2. 检查日志文件
3. 提交 Issue 描述问题

---
作者：https://t.me/HY499
交流群：https://t.me/amlhcgj
**免责声明**: 本工具仅供学习和研究使用，使用者需自行承担使用风险，开发者不承担任何法律责任。
