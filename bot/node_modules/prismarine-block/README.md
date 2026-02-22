# prismarine-block
[![NPM version](https://img.shields.io/npm/v/prismarine-block.svg)](http://npmjs.com/package/prismarine-block)
[![Build Status](https://github.com/PrismarineJS/prismarine-block/workflows/CI/badge.svg)](https://github.com/PrismarineJS/prismarine-block/actions?query=workflow%3A%22CI%22)

Represent a minecraft block with its associated data

## Usage

```js
const registry = require('prismarine-registry')('1.8')
const Block = require('prismarine-block')(registry)

const stoneBlock = new Block(registry.blocksByName.stone, registry.biomesByName.plains, /* meta */ 0)

console.log(stoneBlock)

// can you harvest stone with an iron pickaxe?
console.log(stoneBlock.canHarvest(257))

// how many milliseconds does it takes in usual conditions? (on ground, not in water and not in creative mode)
console.log(stoneBlock.digTime(257))

```

## API

See [doc/API.md](doc/API.md)

## History

### 1.21.0
* [Add isWaterlogged to API (#105)](https://github.com/PrismarineJS/prismarine-block/commit/bf84ca682255db995dfaba23e03209cc5af3ead6) (thanks @extremeheat)

### 1.20.0
* [Bump mocha from 10.8.2 to 11.0.1 (#104)](https://github.com/PrismarineJS/prismarine-block/commit/21e8ea2128df9bb90b59aa58fa491d6dd6031a3f) (thanks @dependabot[bot])
* [Add support for Bedrock edition block hashes (#97)](https://github.com/PrismarineJS/prismarine-block/commit/bc8a7af40438d6d6c715fc8d1e1da8a087c588ad) (thanks @FreezeEngine)

### 1.19.0
* [Update npm-publish.yml](https://github.com/PrismarineJS/prismarine-block/commit/faed7f0390d3f4fd0b15e24193463ed111dbc69a) (thanks @rom1504)

### 1.18.0
* [Fix false value handling in fromProperties for post flatenning versions (#98)](https://github.com/PrismarineJS/prismarine-block/commit/1514a1dcd12984016a5fd360009dd3811ae54f66) (thanks @zardoy)
* [fix version used in block entity (#99)](https://github.com/PrismarineJS/prismarine-block/commit/05aed2ecee7f427b332b0682618368e61c45e1eb) (thanks @rom1504)
* [Allow two variations of syntax in fromString (#96)](https://github.com/PrismarineJS/prismarine-block/commit/52fda556ca39d5d3848ddea297c1409b615301d8) (thanks @Flonja)

### 1.17.1
* [Export Block class declaration (#91)](https://github.com/PrismarineJS/prismarine-block/commit/06ef318525aa92b57b400e0ee899231a4a737bec) (thanks @IceTank)
* [Bump standard from 16.0.4 to 17.1.0 (#83)](https://github.com/PrismarineJS/prismarine-block/commit/00cb8a9a6b810f1bcf7a6482b9a25554d7c39a70) (thanks @dependabot[bot])
* [use nmd supportFeature (#60)](https://github.com/PrismarineJS/prismarine-block/commit/83a74fc3877197a6383665f7e121081e54f36e86) (thanks @u9g)
* [Add command gh workflow allowing to use release command in comments (#90)](https://github.com/PrismarineJS/prismarine-block/commit/e9955a02d44570111ad0f72c52e61c3b1f5be72f) (thanks @rom1504)

### 1.17.0

* Support for multi-sided signs (thanks @PondWader)

### 1.16.3

* really

### 1.16.2

* correct

### 1.16.1

* fix mcdata dep

### 1.15.0

* Effect names were normalized
* Metadata to 0 by default

### 1.14.1

* Legacy version fixes

### 1.14.0

* Add .stateId, .fromProperties, .getProps for all versions

### 1.13.1

* Change blockEntity version handling

### 1.13.0

* Add sign block entity implementation

### 1.12.0

* Updated to support `prismarine-registry`. To use, instead of passing a string to prismarine-biome's default function export, pass an instance of `prismarine-registry`.
* block entity support

### 1.11.0

* support bedrock

### 1.10.3

* use normalized enchant rather than custom format (@u9g #41)

### 1.10.2

* remove debug code

### 1.10.1

* Fix ternary operator for bedrock name check

### 1.10.0

* 1.17.0 support (thanks @Archengius and @the9g)

### 1.9.0

* added `block.getProperties()` type definitions.
* added instant breaking support
* added `Block.fromProperties()` constructor.

### 1.8.0

* Efficiency fix on versions below 1.13

### 1.7.3

* Fix effectLevel not working in digTime. (@Naomi-alt)

### 1.7.2

* add testing for shapes, make it more robust to missing data

### 1.7.1

* fix canHarvest when no harvestTools required (thanks @Garfield100)

### 1.7.0

* Add getProperties (thanks @Karang)

### 1.6.0

* Add enchantments and effects to dig time computation (thanks @Karang)

### 1.5.1

* Make Block.fromStateId work for all versions

### 1.5.0

* Fix block metadata for 1.13+

### 1.4.0

* add block shapes (thanks @Karang)

### 1.3.0

* add typescript definitions (thanks @IdanHo)

### 1.2.0

* Prevent data from being shared to avoid conflicts across multiple versions (thanks @hornta)

### 1.1.1

* use the minStateId if passing the blockType

### 1.1.0

* add block state id feature (for >= 1.13)

### 1.0.1

* bump mcdata

### 1.0.0

* bump dependencies

### 0.1.0

* Import from mineflayer
