# prismarine-realms
[![NPM version](https://img.shields.io/npm/v/prismarine-realms.svg)](http://npmjs.com/package/prismarine-realms)
[![Build Status](https://github.com/PrismarineJS/prismarine-realms/workflows/CI/badge.svg)](https://github.com/PrismarineJS/prismarine-realms/actions?query=workflow%3A%22CI%22)
[![Discord](https://img.shields.io/badge/chat-on%20discord-brightgreen.svg)](https://discord.gg/GsEFRM8)
[![Try it on gitpod](https://img.shields.io/badge/try-on%20gitpod-brightgreen.svg)](https://gitpod.io/#https://github.com/PrismarineJS/prismarine-realms)

Minecraft Realm interface for Minecraft Java and Bedrock editions, providing a stable API to start/stop Realms, and obtain Realm information such as connection addresses.

Minecraft Realms is a subscription based service provided by Mojang where users can host, create and manage their own private Minecraft servers.

## Installation
```shell
npm install prismarine-realms
```

## Usage

### RealmAPI

#### .from(authflow: Authflow, platform: 'bedrock' | 'java')

Takes an **Authflow** instance from [prismarine-auth](https://github.com/PrismarineJS/prismarine-auth), you can see the documentation for this [here.](https://github.com/PrismarineJS/prismarine-auth#authflow)

### Example

```js
const { Authflow } = require('prismarine-auth') 
const { RealmAPI } = require('prismarine-realms')

const authflow = new Authflow()

const api = RealmAPI.from(authflow, 'bedrock') // or 'java'

// Returns a list of Realms the authenticating account has joined or owns.
await api.getRealms().then(console.log)
```

## Documentation

See [API Documentation](./docs/API.md#realmsapi)