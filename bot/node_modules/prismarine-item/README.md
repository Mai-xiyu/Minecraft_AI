# prismarine-item
[![NPM version](https://img.shields.io/npm/v/prismarine-item.svg)](http://npmjs.com/package/prismarine-item)
[![Build Status](https://github.com/PrismarineJS/prismarine-item/workflows/CI/badge.svg)](https://github.com/PrismarineJS/prismarine-item/actions?query=workflow%3A%22CI%22)

Represent a minecraft item with its associated data

## Usage

```js
const Item = require('prismarine-item')('1.8')

const ironShovelItem = new Item(256, 1)
console.log(ironShovelItem)

const notchItem = Item.toNotch(ironShovelItem)
console.log(notchItem)
console.log(Item.fromNotch(notchItem))
```

## API

### Item(type, count[, metadata, nbt, stackId, sentByServer])

* sentByServer - whether this item was sent by the server to the client, so default 
  initialization will not be done on the item. For example, tools will not have the
  default item NBT written to them.

#### Item.toNotch(item[, serverAuthoritative])

Take an `Item` instance and returns it in the format of the minecraft packets.
- serverAuthoritative: Whether the server is using server authoritative inventory (whether or not to write a Stack ID)

#### Item.fromNotch(item[, stackId])

Take an `item` in the format of the minecraft packets and return an `Item` instance.
- stackId for bedrock items before 1.16.220

### Item.anvil(itemOne, itemTwo, creative[, newName])

Take two seperate `item` instances, and makes one item using the same combining done by the vanilla anvil

### Item.equal(itemOne, itemTwo[, matchStackSize, matchNbt])

`itemOne` - first item

`itemTwo` - second item

`matchStackSize` - whether to check for count equality

`matchNbt` - wether to check for NBT equality

Checks equality between two items based on itemType, count, metadata, and stringified nbt

#### item.type

Numerical id.

#### item.count

#### item.metadata

Number which represents different things depending on the item.
See http://www.minecraftwiki.net/wiki/Data_values#Data

#### item.nbt

Buffer.

#### item.stackId

The stack ID of the item, if the version supports Stack IDs.

#### item.name

#### item.displayName

#### item.stackSize

#### item.equal(otherItem)

Return true if items are equal.

#### item.durabilityUsed

A getter/setter for abstracting the underlying nbt

#### item.customName

the item's custom name (ie. anvil name)

#### item.customLore

the item's custom lore (ie. set in give command)

#### item.enchants

#### get item.enchants(): { name: string, lvl: number }[]

Returns an array of enchants on the Item with their name and level

#### set item.enchants({ name: string, lvl: number }[])

Updates the Item's NBT enchantments based on assigned array

#### get item.blocksCanPlaceOn(): [name][]
#### set item.blocksCanPlaceOn(blockNames: string[])
In adventure mode, the list of block names (as strings) that this Item can be placed on

#### get item.blocksCanDestroy(): [name][]
#### set item.blocksCanDestroy(blockNames: string[])

In adventure mode, the list of block names (as strings) that this Item can be used to break

#### item.repairCost

A getter/setter for abstracting the underlying nbt.
See https://minecraft.gamepedia.com/Anvil_mechanics#Anvil_Uses

#### item.spawnEggMobName

If the current item is a type of Spawn Egg, the protocol name of the entity that will be spawned. For example, a zombie spawn egg on 1.8 will return `Zombie`.

#### item.maxDurability

Max durability for the item, if it supports durability

## History

### 1.16.0
* [Fix durabilityUsed for items with components (#123)](https://github.com/PrismarineJS/prismarine-item/commit/70fc068ffe73706d97b5b0dced0f15056e369fa4) (thanks @rom1504)
* [Bump mocha from 10.8.2 to 11.0.1 (#120)](https://github.com/PrismarineJS/prismarine-item/commit/5f72f300f431406fa3804b24efe06b9a84610960) (thanks @dependabot[bot])
* [Fix typing error in loader function (#122)](https://github.com/PrismarineJS/prismarine-item/commit/7d4cd63f5ffdc50670a3a2f817653c7a58d66725) (thanks @extremeheat)

### 1.15.0
* [1.20.5 (#118)](https://github.com/PrismarineJS/prismarine-item/commit/09815d2778dec72665a16bf6d60ae75d53fb7988) (thanks @extremeheat)
* [Bump @types/node from 20.14.15 to 22.3.0 (#117)](https://github.com/PrismarineJS/prismarine-item/commit/094e32a5b2f7c581ddea4a8d605276aa389c9285) (thanks @dependabot[bot])

### 1.14.0
* [Add `maxDurability` field, fix handling item sent by server with new `sentByServer` arg (#106)](https://github.com/PrismarineJS/prismarine-item/commit/d36111d1a754ed9a3db152465b7a930b6582474f) (thanks @extremeheat)

### 1.13.1
* [Fix null item handling in toNotch (#103)](https://github.com/PrismarineJS/prismarine-item/commit/0fd5781c1c539207aa932bb637c074e671196f60) (thanks @extremeheat)

### 1.13.0
* [Bedrock support (#86)](https://github.com/PrismarineJS/prismarine-item/commit/854c357c4835cff74d9c9812b599528103bf2976) (thanks @CreeperG16)

### 1.12.3
* [add commands workflow (#99)](https://github.com/PrismarineJS/prismarine-item/commit/a4f5d593be8a80fbe539369efe2d1127c9785583) (thanks @extremeheat)
* [Update to node 18.0.0 (#98)](https://github.com/PrismarineJS/prismarine-item/commit/52098ca2b0a9eafa6bcde3cdfb3c2315bab258a5) (thanks @rom1504)

## 1.12.2

* Fix types (thanks @TigerbyteDev and @u9g)

## 1.12.1

* Fix publish

## 1.12.0

* uses registry instead of mcData (thanks @Epirito)

## 1.11.5

* Update mcdata

## 1.11.4

* Use mcData.items instead of mcData.findItemOrBlockById()

## 1.11.3

* Use supportFeature from mcdata

## 1.11.2

* Add checks for enchantment name retrieval (#53) @firejoust
* Bump prismarine-nbt from 1.6.0 to 2.0.0 (#49)

## 1.11.1

* fix customLore

## 1.11.0

* fix typings
* add .customLore
* .customName now returns null when there is no custom name

## 1.10.1

* update typings (thanks @stzups)

## 1.10.0

* add item.spawnEggMobName (thanks @U9G)

## 1.9.1

* fix item present detection (thanks @U9G)

## 1.9.0

* Revise typings (thanks @extremeheat)
* Revise deps (thanks @rom1504)
* Correctly identify null items in MC 1.13 (thanks @u9g)

## 1.8.0

* add matchStackSize option on Item.equal (thanks @u9g)

## 1.7.0

* Item.equal checks nbt equality (thanks @u9g)

## 1.6.0

* Item.anvil added, along with a ton of getters & setters for Item (thanks @u9g)

### 1.5.0

* 1.16 support (thanks @DrakoTrogdor)

### 1.4.0

* typescripts definitions (thanks @IdanHo)

### 1.3.0

* 1.15 support

### 1.2.0

* 1.14 support

### 1.1.1

* allow unknown items

### 1.1.0

* 1.13 support

### 1.0.2

* make nbt default to null
* display the item id if it is not found in minecraft data

### 1.0.1

* bump mcdata

### 1.0.0

* bump dependencies

### 0.0.0

* Import from mineflayer
