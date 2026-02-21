# Minecraft AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.1.0--Improved-green.svg)]()
[![Node](https://img.shields.io/badge/Node.js-%3E%3D14-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/Python-%3E%3D3.8-blue.svg)]()

[English](README.md)

基于大语言模型的 Minecraft AI 代理系统。AI 可以在 Minecraft 中自主探索、采集资源、建造建筑、合成物品、战斗等——没有步数限制，持续运行直到你手动停止。

**作者：** 饩雨 (God_xiyu | Mai_xiyu)  
**邮箱：** mai_xiyu@vip.qq.com  
**版本：** v2.1.0-Improved

---

## 主要特性

- **支持任意 OpenAI 兼容 LLM** — DeepSeek、GPT-4o、通义千问、Kimi、本地模型等
- **22 种动作类型** — 移动、采矿、合成、战斗、进食、钓鱼、熔炼、箱子操作、睡觉、跟随玩家、探索等
- **无限自主循环** — AI 持续运行，支持手动停止 + 连续错误自动暂停（无步数限制）
- **全异步 GUI** — 所有 HTTP 请求在工作线程中执行，界面永不卡顿
- **记忆与学习系统** — 记住历史动作，从成功/失败中学习
- **模式识别与缓存** — 加速重复场景的决策
- **执行结果反馈** — 每次动作的结果（成功/失败 + 详情）都会反馈给 LLM，使其能调整策略
- **LLM 连接测试** — 一键验证 API Key、Base URL 和模型是否正常工作
- **双语 GUI (i18n)** — 运行时自由切换中文和英文
- **自定义任务** — 创建、保存和复用任务预设
- **实时监控** — 实时 Bot 状态、日志输出和运行时任务切换

## 系统架构

```
┌─────────────────────────────────────────────┐
│              PyQt6 GUI (main_window.py)      │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ 控制面板  │ │ 配置面板  │ │ 赞助页面    │ │
│  └────┬──────┘ └──────────┘ └──────────────┘ │
│       │ HttpWorker / BotReadyWorker (QThread) │
└───────┼───────────────────────────────────────┘
        │ HTTP (异步)
┌───────▼───────────────────────────────────────┐
│           AIThread (QThread)                   │
│  ┌─────────┐ ┌────────┐ ┌──────────────────┐  │
│  │ Agent   │ │ 记忆   │ │ 模式识别 / 缓存  │  │
│  │ (LLM)   │ │        │ │ 学习系统         │  │
│  └────┬────┘ └────────┘ └──────────────────┘  │
└───────┼────────────────────────────────────────┘
        │ HTTP POST /bot/action
┌───────▼───────────────────────────────────────┐
│        Node.js Bot 服务器 (Express:3002)       │
│  ┌──────────┐ ┌────────────┐ ┌─────────────┐  │
│  │mineflayer│ │ pathfinder │ │ collectBlock│  │
│  └──────────┘ └────────────┘ └─────────────┘  │
└───────┬────────────────────────────────────────┘
        │ Minecraft 协议
┌───────▼──────────┐
│  Minecraft 服务器 │
└──────────────────┘
```

## 安装

### 前置要求

- **Python 3.8+**（推荐 3.11）
- **Node.js 14+**
- **Minecraft Java 版**（1.16.5 – 1.21.1）

### 安装步骤

```bash
# 克隆项目
git clone <repo-url>
cd Minecraft_AI

# 安装 Python 依赖（run.py 启动时也会自动检查）
pip install requests PyQt6

# 安装 Bot 依赖
cd bot
npm install
cd ..
```

## 快速开始

### 1. 启动 Minecraft

1. 启动 Minecraft Java 版
2. 创建或打开一个世界
3. 按 **ESC → 对局域网开放**，记下显示的端口号

### 2. 启动 AI

```bash
python run.py
```

### 3. 配置

在 **配置** 选项卡中：

| 设置项 | 说明 |
|--------|------|
| **主机 / 端口** | Minecraft 服务器地址（默认 `localhost:25565`） |
| **API Key** | 你的 LLM 服务商 API 密钥 |
| **Base URL** | OpenAI 兼容端点（如 `https://api.deepseek.com/v1`） |
| **模型** | 模型名称（如 `deepseek-chat`、`gpt-4o-mini`、`kimi-k2-turbo-preview`） |
| **任务** | 初始任务（或选择"自由行动"让 AI 自由发育） |
| **步间延迟** | AI 每步之间的等待秒数 |
| **温度** | LLM 创造性（0.0 – 2.0） |
| **最大 Token** | 最大回复长度 |
| **启用缓存** | 启用响应缓存以加速 |
| **启用预测** | 启用基于模式的动作预测 |

配置完成后点击 **保存配置**。

### 4. 测试与运行

1. 点击 **测试连接** — 验证 Bot 服务器是否可达
2. 点击 **测试LLM** — 验证 API Key 和模型是否正常工作
3. 点击 **启动AI** — Bot 加入 Minecraft 世界并开始自主行动
4. 点击 **停止AI** — 随时停止

## 可用动作（22 种）

| 动作 | 参数 | 说明 |
|------|------|------|
| `moveTo` | x, y, z | 移动到指定坐标 |
| `collect` | blockType, count?, radius? | 采集方块/资源 |
| `placeBlock` | itemName, x, y, z | 放置方块 |
| `dig` | x, y, z | 挖掘方块 |
| `attack` | target | 攻击实体 |
| `jumpAttack` | target | 跳跃攻击（暴击） |
| `lookAt` | x, y, z | 看向指定位置 |
| `equip` | itemName, destination? | 装备物品 |
| `unequip` | destination? | 卸下装备 |
| `craft` | itemName, count? | 合成物品 |
| `chat` | message | 发送聊天消息 |
| `useHeldItem` | — | 使用手持物品 |
| `wait` | ticks? | 等待 |
| `dropItem` | itemName, count? | 丢弃物品 |
| `eat` | itemName? | 进食（不指定则自动选择食物） |
| `fish` | duration? | 钓鱼 |
| `smelt` | itemName, fuelName?, count? | 熔炼物品 |
| `openChest` | x, y, z, chestAction | 打开/查看箱子 |
| `depositItem` | x, y, z, itemName, count? | 将物品存入箱子 |
| `withdrawItem` | x, y, z, itemName, count? | 从箱子取出物品 |
| `sleep` | — | 在附近的床上睡觉 |
| `followPlayer` | playerName, distance? | 跟随玩家 |
| `explore` | radius? | 探索并扫描周围环境 |

## AI 决策流程

1. **获取 Bot 状态** — 位置、血量、饥饿值、物品栏、附近实体和方块
2. **查询缓存** — 如果之前遇到过相同情况，复用决策
3. **模式识别** — 如果有高置信度的模式匹配，直接使用
4. **调用 LLM** — 发送状态 + 对话历史 + 记忆 + 学习反馈
5. **解析 & 验证** — 提取 JSON 动作，验证必要参数
6. **执行** — POST 动作到 Bot 服务器
7. **结果反馈** — 将成功/失败消息追加到对话历史，让 LLM 从每次动作中学习

这个反馈循环至关重要：例如 `craft crafting_table` 因为没有先制作木板而失败时，LLM 会看到错误消息并相应调整计划。

## 自动暂停

AI 在 **连续 5 次错误** 后自动暂停（可配置）。弹出对话框说明情况。修复问题后（如 Bot 断连、LLM 额度耗尽），可以重新启动。

## 配置文件

所有设置存储在 `config.json` 中：

```json
{
  "minecraft": {
    "host": "localhost",
    "port": 25565,
    "username": "AI_Player",
    "version": "1.20.1"
  },
  "server": {
    "host": "localhost",
    "port": 3002
  },
  "ai": {
    "api_key": "sk-...",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "initial_task": "3. 建造房屋",
    "delay": 2,
    "temperature": 0.7,
    "max_tokens": 2048,
    "use_cache": true,
    "use_prediction": true
  },
  "gui": {
    "language": "zh"
  }
}
```

## 项目结构

```
Minecraft_AI/
├── run.py                      # 入口（依赖检查 → 启动 GUI）
├── config.json                 # 配置文件
├── ai/
│   ├── agent.py                # 核心 AI 代理（LLM 循环、结果反馈）
│   ├── prompts.py              # 系统提示词 & 状态格式化
│   ├── llm_client.py           # OpenAI 兼容 LLM 客户端
│   ├── memory.py               # 长期记忆系统
│   ├── learning.py             # 动作成功/失败学习
│   ├── cache_system.py         # 响应缓存
│   └── pattern_recognition.py  # 模式识别预测
├── bot/
│   ├── index.js                # Express 服务器 + Bot 管理
│   ├── actions.js              # 全部 22 种动作实现
│   ├── crafting.js             # 合成逻辑
│   ├── inventory.js            # 物品栏管理
│   └── package.json
├── gui/
│   ├── main_window.py          # PyQt6 主窗口（异步工作线程）
│   ├── i18n.py                 # 国际化（中/英）
│   ├── main.py                 # GUI 入口
│   └── sponsor_page.py         # 赞助页面
└── resources/
    └── icon.ico
```

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 无法启动 GUI | 确保已安装 `PyQt6` 和 `requests` |
| 无法连接 Minecraft | 检查局域网已开放、端口正确、防火墙放行 |
| Bot 加入了但 AI 不动 | 点击 **测试LLM** 验证 API 连接 |
| AI 重复执行同一个失败动作 | 已在 v2.1.0 修复 — 执行结果现在会反馈给 LLM |
| 连续 5 次错误后自动暂停 | 检查 Bot 连接和 LLM 配置，然后重新启动 |
| `Cannot find module 'mineflayer'` | 运行 `cd bot && npm install` |

## 更新日志

### v2.1.0-Improved（当前版本）

- **全异步 GUI** — 所有 HTTP 请求在 QThread 工作线程中执行，界面永不卡顿
- **无限 AI 循环** — 无步数限制；手动停止 + 连续错误自动暂停
- **8 个新动作** — 进食、钓鱼、熔炼、箱子操作、睡觉、跟随玩家、探索
- **执行结果反馈** — 动作结果反馈到 LLM 对话历史
- **LLM 连接测试按钮** — 从 GUI 一键验证 API Key / Base URL / 模型
- **增强系统提示词** — 生存优先级、资源管理、自由发育模式
- **可配置缓存与预测** — 从 GUI 切换，持久化到 config.json

### v1.2.7

- 多语言 GUI 支持（i18n）
- 复合动作（`jumpAttack`）
- 增强状态信息（游戏时间、耐久度、敌对状态）
- 自动依赖检查
- 视觉学习系统（实验性）

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 支持

如果你觉得这个项目有用，欢迎给仓库点个 ⭐，或通过应用内的赞助页面支持作者。
