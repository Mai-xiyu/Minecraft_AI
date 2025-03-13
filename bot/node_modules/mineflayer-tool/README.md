<h1 align="center">Mineflayer-Tool</h1>
<p align="center"><i>A tool/weapon selection Mineflayer plugin for automatically selecting the best tool to use for a specific task.</i></p>

<p align="center">
  <img src="https://github.com/TheDudeFromCI/mineflayer-tool/workflows/Build/badge.svg" />
  <img src="https://img.shields.io/npm/v/mineflayer-tool" />
  <img src="https://img.shields.io/github/repo-size/TheDudeFromCI/mineflayer-tool" />
  <img src="https://img.shields.io/npm/dm/mineflayer-tool" />
  <img src="https://img.shields.io/github/contributors/TheDudeFromCI/mineflayer-tool" />
  <img src="https://img.shields.io/github/license/TheDudeFromCI/mineflayer-tool" />
</p>

---

### Getting Started

This plugin is built using Node and can be installed using:
```bash
npm install --save mineflayer-tool
```

### Simple Bot

The brief description goes here.

```js
const mineflayer = require('mineflayer')
const toolPlugin = require('mineflayer-tool').plugin

const bot = mineflayer.createBot({ username: 'MiningTool_Bot' })
bot.loadPlugin(toolPlugin)

bot.on('spawn', async () => {
  const blockPos = bot.entity.position.offset(0, -1, 0)
  const block = bot.blockAt(blockPos)

  await bot.tool.equipForBlock(block, {})
  await bot.dig(block)
 })
```

### Documentation

[API](https://github.com/TheDudeFromCI/mineflayer-tool/blob/master/docs/api.md)

[Examples](https://github.com/TheDudeFromCI/mineflayer-tool/tree/master/examples)

### License

This project uses the [MIT](https://github.com/TheDudeFromCI/mineflayer-tool/blob/master/LICENSE) license.

### Contributions

This project is accepting PRs and Issues. See something you think can be improved? Go for it! Any and all help is highly appreciated!

For larger changes, it is recommended to discuss these changes in the issues tab before writing any code. It's also preferred to make many smaller PRs than one large one, where applicable.
