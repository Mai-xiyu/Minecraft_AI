# Minecraft AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.1.0--Improved-green.svg)]()
[![Node](https://img.shields.io/badge/Node.js-%3E%3D14-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/Python-%3E%3D3.8-blue.svg)]()

[中文文档](Readme_CN.md)

An intelligent Minecraft AI agent system powered by large language models. The AI agent can autonomously explore, gather resources, build structures, craft items, fight mobs, and much more in Minecraft — with no step limit, running continuously until you say stop.

**Author:** 饩雨 (God_xiyu | Mai_xiyu)  
**Email:** mai_xiyu@vip.qq.com  
**Version:** v2.1.0-Improved

---

## Key Features

- **Any OpenAI-compatible LLM** — DeepSeek, GPT-4o, Qwen, Kimi, local models, etc.
- **22 action types** — movement, mining, crafting, combat, eating, fishing, smelting, chest operations, sleeping, following players, exploring, and more
- **Infinite autonomous loop** — AI runs continuously with manual stop + auto-pause on consecutive errors (no step limit)
- **Fully async GUI** — all HTTP calls run off the main thread; the UI never freezes
- **Memory & learning system** — remembers past actions, learns from success/failure
- **Pattern recognition & caching** — speeds up repeated decisions
- **Execution feedback loop** — every action result (success/failure + details) is fed back to the LLM so it can adapt strategy
- **LLM connection test** — one-click button to verify your API key, base URL, and model work
- **Bilingual GUI (i18n)** — switch between English and Chinese at runtime
- **Custom tasks** — create, save, and reuse task presets
- **Real-time monitoring** — live bot status, log output, and runtime task switching

## Architecture

```
┌─────────────────────────────────────────────┐
│              PyQt6 GUI (main_window.py)      │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ Control   │ │ Config   │ │ Sponsor      │ │
│  │ Panel     │ │ Panel    │ │ Page         │ │
│  └────┬──────┘ └──────────┘ └──────────────┘ │
│       │ HttpWorker / BotReadyWorker (QThread) │
└───────┼───────────────────────────────────────┘
        │ HTTP (async)
┌───────▼───────────────────────────────────────┐
│           AIThread (QThread)                   │
│  ┌─────────┐ ┌────────┐ ┌──────────────────┐  │
│  │ Agent   │ │ Memory │ │ Pattern / Cache  │  │
│  │ (LLM)   │ │        │ │ Learning         │  │
│  └────┬────┘ └────────┘ └──────────────────┘  │
└───────┼────────────────────────────────────────┘
        │ HTTP POST /bot/action
┌───────▼───────────────────────────────────────┐
│        Node.js Bot Server (Express:3002)       │
│  ┌──────────┐ ┌────────────┐ ┌─────────────┐  │
│  │mineflayer│ │ pathfinder │ │ collectBlock│  │
│  └──────────┘ └────────────┘ └─────────────┘  │
└───────┬────────────────────────────────────────┘
        │ Minecraft Protocol
┌───────▼──────────┐
│  Minecraft Server │
└──────────────────┘
```

## Installation

### Prerequisites

- **Python 3.8+** (3.11 recommended)
- **Node.js 14+**
- **Minecraft Java Edition** (1.16.5 – 1.21.1)

### Steps

```bash
# Clone the project
git clone <repo-url>
cd Minecraft_AI

# Install Python dependencies (run.py also auto-checks on startup)
pip install requests PyQt6

# Install Bot dependencies
cd bot
npm install
cd ..
```

## Quick Start

### 1. Start Minecraft

1. Launch Minecraft Java Edition
2. Create or open a world
3. Press **ESC → Open to LAN** and note the port number

### 2. Launch the AI

```bash
python run.py
```

### 3. Configure

In the **Config** tab:

| Setting | Description |
|---------|-------------|
| **Host / Port** | Minecraft server address (default `localhost:25565`) |
| **API Key** | Your LLM provider's API key |
| **Base URL** | OpenAI-compatible endpoint (e.g. `https://api.deepseek.com/v1`) |
| **Model** | Model name (e.g. `deepseek-chat`, `gpt-4o-mini`, `kimi-k2-turbo-preview`) |
| **Task** | Starting task (or choose "自由行动" for free play) |
| **Delay** | Seconds between AI steps |
| **Temperature** | LLM creativity (0.0 – 2.0) |
| **Max Tokens** | Maximum reply length |
| **Use Cache** | Enable response caching for speed |
| **Use Prediction** | Enable pattern-based action prediction |

Click **Save Config** when done.

### 4. Test & Run

1. Click **Test Connection** to verify the bot server is reachable
2. Click **Test LLM** to verify your API key and model work correctly
3. Click **Start AI** — the bot joins the Minecraft world and begins acting autonomously
4. Click **Stop AI** to halt at any time

## Available Actions (22 types)

| Action | Parameters | Description |
|--------|-----------|-------------|
| `moveTo` | x, y, z | Move to coordinates |
| `collect` | blockType, count?, radius? | Gather blocks / resources |
| `placeBlock` | itemName, x, y, z | Place a block |
| `dig` | x, y, z | Break a block |
| `attack` | target | Attack an entity |
| `jumpAttack` | target | Critical hit (jump attack) |
| `lookAt` | x, y, z | Look at position |
| `equip` | itemName, destination? | Equip an item |
| `unequip` | destination? | Unequip |
| `craft` | itemName, count? | Craft an item |
| `chat` | message | Send a chat message |
| `useHeldItem` | — | Use held item |
| `wait` | ticks? | Wait |
| `dropItem` | itemName, count? | Drop an item |
| `eat` | itemName? | Eat food (auto-selects if omitted) |
| `fish` | duration? | Fish with a rod |
| `smelt` | itemName, fuelName?, count? | Smelt in a furnace |
| `openChest` | x, y, z, chestAction | Open / view a chest |
| `depositItem` | x, y, z, itemName, count? | Store item in chest |
| `withdrawItem` | x, y, z, itemName, count? | Take item from chest |
| `sleep` | — | Sleep in a nearby bed |
| `followPlayer` | playerName, distance? | Follow a player |
| `explore` | radius? | Explore and scan surroundings |

## How the AI Decides

1. **Get bot state** — position, health, hunger, inventory, nearby entities & blocks
2. **Check cache** — if an identical situation was seen before, reuse the decision
3. **Check pattern recognition** — if a high-confidence pattern matches, use it
4. **Call LLM** — send state + conversation history + memory + learning feedback
5. **Parse & validate** — extract JSON action, validate required parameters
6. **Execute** — POST action to the bot server
7. **Feed back result** — success/failure message is appended to conversation history so the LLM learns from each action

This feedback loop is critical: if `craft crafting_table` fails because planks haven't been made yet, the LLM sees the error and adjusts its plan accordingly.

## Auto-Pause

The AI automatically pauses after **5 consecutive errors** (configurable). A dialog pops up explaining the situation. After fixing the issue (e.g. bot disconnected, LLM quota exhausted), you can restart.

## Configuration File

All settings are stored in `config.json`:

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
    "language": "en"
  }
}
```

## Project Structure

```
Minecraft_AI/
├── run.py                      # Entry point (dependency check → GUI)
├── config.json                 # Configuration file
├── ai/
│   ├── agent.py                # Core AI agent (LLM loop, feedback)
│   ├── prompts.py              # System prompt & state formatting
│   ├── llm_client.py           # OpenAI-compatible LLM client
│   ├── memory.py               # Long-term memory system
│   ├── learning.py             # Action success/failure learning
│   ├── cache_system.py         # Response caching
│   └── pattern_recognition.py  # Pattern-based prediction
├── bot/
│   ├── index.js                # Express server + bot management
│   ├── actions.js              # All 22 action implementations
│   ├── crafting.js             # Crafting logic
│   ├── inventory.js            # Inventory management
│   └── package.json
├── gui/
│   ├── main_window.py          # PyQt6 main window (async workers)
│   ├── i18n.py                 # Internationalization (en/zh)
│   ├── main.py                 # GUI entry point
│   └── sponsor_page.py         # Sponsor page
└── resources/
    └── icon.ico
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Cannot start GUI | Ensure `PyQt6` and `requests` are installed |
| Cannot connect to Minecraft | Check LAN is open, port matches, firewall allows |
| Bot joins but AI doesn't act | Click **Test LLM** to verify API connection |
| AI repeats the same failed action | Fixed in v2.1.0 — results now feed back to the LLM |
| Auto-pause after 5 errors | Check bot connection and LLM config, then restart |
| `Cannot find module 'mineflayer'` | Run `cd bot && npm install` |

## Changelog

### v2.1.0-Improved (Current)

- **Fully async GUI** — all HTTP requests run in QThread workers; UI never freezes
- **Infinite AI loop** — no step limit; manual stop + auto-pause on consecutive errors
- **8 new actions** — eat, fish, smelt, chest operations, sleep, follow player, explore
- **Execution feedback loop** — action results fed back to LLM conversation history
- **LLM connection test button** — verify API key / base URL / model from the GUI
- **Enhanced system prompt** — survival priorities, resource management, free-play mode
- **Configurable cache & prediction** — toggle from GUI, persisted to config.json

### v1.2.7

- Multilingual GUI support (i18n)
- Compound action (`jumpAttack`)
- Enhanced state information (timeOfDay, durability, isHostile)
- Automatic dependency checking
- Vision learning system (experimental)

## License

This project is licensed under the [MIT License](LICENSE).

## Support

If you find this project useful, consider giving the repo a ⭐ or supporting the author via the sponsor page in the app.
