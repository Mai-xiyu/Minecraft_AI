# prismarine-auth
[![NPM version](https://img.shields.io/npm/v/prismarine-auth.svg)](http://npmjs.com/package/prismarine-auth)
[![Build Status](https://github.com/PrismarineJS/prismarine-auth/workflows/CI/badge.svg)](https://github.com/PrismarineJS/prismarine-auth/actions?query=workflow%3A%22CI%22)
[![Official Discord](https://img.shields.io/static/v1.svg?label=PrismarineJS&message=Discord&color=blue&logo=discord)](https://discord.gg/GsEFRM8)
[![Try it on gitpod](https://img.shields.io/badge/try-on%20gitpod-brightgreen.svg)](https://gitpod.io/#https://github.com/PrismarineJS/prismarine-auth)

Quickly and easily obtain auth tokens to authenticate with Microsoft/Xbox/Minecraft/Mojang

## Installation
```shell
npm install prismarine-auth
```

## Usage

### Authflow
**Parameters**
- username? {String} - Username for authentication
- cacheDirectory? {String | Function} - Where we will store your tokens (optional) or a factory function that returns a cache.
- options {Object?}
    - [flow] {enum} Required if options is specified - see [API.md](docs/API.md) for options
    - [forceRefresh] {boolean} - Clear all cached tokens for the specified `username` to get new ones on subsequent token requests
    - [password] {string} - If passed we will do password based authentication.
    - [authTitle] {string} - See the [API.md](docs/API.md)
    - [deviceType] {string} - See the [API.md](docs/API.md)
- onMsaCode {Function} - (For device code auth) What we should do when we get the code. Useful for passing the code to another function.

### Examples

### getMsaToken
```js
const { Authflow, Titles } = require('prismarine-auth')

const userIdentifier = 'unique identifier for caching'
const cacheDir = './' // You can leave this as undefined unless you want to specify a caching directory
const flow = new Authflow(userIdentifier, cacheDir)
// Get a auth token, then log it
flow.getMsaToken().then(console.log)
```

**Note**: By default, this library will authenticate as Minecraft for Nintendo Switch, with a `flow` set to `live`. For non-Minecraft applications you should
register for Microsoft Azure Oauth token. See https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app#register-an-application for more information on obtaining an Azure token. You then use it with the `msal` flow like this:

```js
const flow = new Authflow(userIdentifier, cacheDir, { flow: 'msal', authTitle: '000-000-000-000' })
```

If `flow` is `live`, the default, then you can only specify existing Microsoft client IDs. This library exposes some default Microsoft client IDs under the exported `Titles` object. See the [types](./index.d.ts) for more information.

### getXboxToken
See [docs/API.md](docs/API.md)


### getMinecraftJavaToken
```js
const { Authflow, Titles } = require('prismarine-auth')

const userIdentifier = 'any unique identifier'
const cacheDir = './' // You can leave this as undefined unless you want to specify a caching directory
const flow = new Authflow(userIdentifier, cacheDir)
// Get a Minecraft Java Edition auth token, then log it
flow.getMinecraftJavaToken({ fetchProfile: true }).then(console.log)
```

### Expected Response
```json
{
    "token": "ey....................",
    "entitlements": {},
    "profile": {
        "id": "b945b6ed99b548675309473a69661b9a",
        "name": "Usname",
        "skins": [ [Object] ],
        "capes": []
    }
}
```

### getMinecraftBedrockToken
See [docs/API.md](docs/API.md) and [example](examples).

### getMinecraftBedrockServicesToken
```js
const { Authflow, Titles } = require('prismarine-auth')

const userIdentifier = 'any unique identifier'
const cacheDir = './' // You can leave this as undefined unless you want to specify a caching directory
const flow = new Authflow(userIdentifier, cacheDir)
// Get a Minecraft Services token, then log it
flow.getMinecraftBedrockServicesToken().then(console.log)
```

### Expected Response
```json
{
    "mcToken": "MCToken eyJ...",
    "validUntil": "1970-01-01T00:00:00.000Z",
    "treatments": [
      "mc-enable-feedback-landing-page",
      "mc-store-enableinbox",
      "mc-nps-freeorpaid-paidaug24",
      // and more
    ],
    "configurations": {
      "validation": {
        "id": "Validation",
        "parameters": {
          "minecraftnetaatest": "false"
        }
      },
      "minecraft": {
        "id": "Minecraft",
        "parameters": {
          "with-spongebobadd-button-noswitch": "true",
          "sfsdfsdfsfss": "true",
          "fsdfd": "true",
          "mc-maelstrom-disable": "true",
          // and more
        }
      }
    },
    "treatmentContext": "mc-sunsetting_5:31118471;mc-..."
}
```

### More
[View more examples here](https://github.com/PrismarineJS/prismarine-auth/tree/master/examples).

See the [types](./index.d.ts) to checkout the full API.

## API

See [docs/API.md](docs/API.md)

## Debugging

You can enable some debugging output using the `DEBUG` enviroment variable. Through node.js, you can add `process.env.DEBUG = 'prismarine-auth'` at the top of your code.


## Testing

Simply run `npm test` or `yarn test`

## License

[MIT](LICENSE)
