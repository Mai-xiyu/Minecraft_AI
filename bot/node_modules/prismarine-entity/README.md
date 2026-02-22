# prismarine-entity
[![NPM version](https://img.shields.io/npm/v/prismarine-entity.svg)](http://npmjs.com/package/prismarine-entity)
[![Build Status](https://github.com/PrismarineJS/prismarine-entity/workflows/CI/badge.svg)](https://github.com/PrismarineJS/prismarine-entity/actions?query=workflow%3A%22CI%22)

Represent a minecraft entity

## Usage

```js
const Entity = require("prismarine-entity")('1.8.9')

const entity = new Entity(0)
console.log(entity)
```

## API

### Entity

Entities represent players, mobs, and objects.

#### entity.id

#### entity.type

Choices:

 * `player`
 * `mob`
 * `object`
 * `global` - lightning
 * `orb` - experience orb.
 * `other` - introduced with a recent Minecraft update and not yet recognized or used by a third-party mod

#### entity.username

If the entity type is `player`, this field will be set.

#### entity.mobType

If the entity type is `mob`, this field will be set.

#### entity.displayName

Field set for mob and object. A long name in multiple words.

#### entity.entityType

Field set for mob and object. The numerical type of the entity (1,2,...)

#### entity.kind

Field set for mob and object. The kind of entity (for example Hostile mobs, Passive mobs, NPCs).

#### entity.name

Field set for mob and object. A short name for the entity.

#### entity.objectType

If the entity type is `object`, this field will be set.

#### entity.count

If the entity type is `orb`, this field will be how much experience you
get from collecting the orb.

#### entity.position

#### entity.velocity

#### entity.yaw

#### entity.pitch

#### entity.height

#### entity.width

#### entity.onGround

#### entity.equipment[5]

Version dependent. 

1.8 Layout:

 * `0` - held item
 * `1` - shoes
 * `2` - legging
 * `3` - torso
 * `4` - head

1.9 and later:

 * `0` - held item
 * `1` - off-hand
 * `2` - shoes
 * `3` - legging
 * `4` - torso
 * `5` - head 

#### entity.heldItem

Equivalent to `entity.equipment[0]`.

#### entity.metadata

See http://wiki.vg/Entities#Entity_Metadata_Format for more details.

#### entity.noClip

#### entity.vehicle

Entity that this entity is riding on

#### entity.passenger

Entity that is riding on this entity

#### entity.health

The health of the player, default: 20

#### entity.food

The food of the player, default: 20

#### entity.elytraFlying

Whether or not the entity is elytra flying.

#### entity.player

The player

#### entity.getCustomName()

returns a `prismarine-chat` ChatMessage object for the name of the entity or null if there isn't one

#### entity.getDroppedItem()

returns a `prismarine-item` Item object for the dropped item, if this is a dropped item, or it will return null

## History

### 2.5.0
* [add Entity.passengers and Entity.vehicle (#75)](https://github.com/PrismarineJS/prismarine-entity/commit/e45c544e7df6ae69239d1d23473c82805d5134b9) (thanks @qwqtoday)
* [Bump @types/node from 20.14.15 to 22.2.0 (#80)](https://github.com/PrismarineJS/prismarine-entity/commit/47b7167630665b1d95b5a88c0e985355a640a012) (thanks @dependabot[bot])

### 2.4.0
* [use getter for  `.heldItem` (#73)](https://github.com/PrismarineJS/prismarine-entity/commit/4694438ab733ea3e2d5414d3330ae295ff85b660) (thanks @szdytom)

### 2.3.1
* [Use console.trace instead of console.log for deprecation message (#71)](https://github.com/PrismarineJS/prismarine-entity/commit/7262fcf02d6656c663f876d513d84cc7266a3903) (thanks @extremeheat)

### 2.3.0
* [Add default elytra flying value (#69)](https://github.com/PrismarineJS/prismarine-entity/commit/f124abd47b42a908a676b91b0fcb55b1fd1a77b9) (thanks @lkwilson)
* [Fix equipment documentation for other versions (#67)](https://github.com/PrismarineJS/prismarine-entity/commit/b2f756de52fa7ceb2675fe9c2f950fa7398bc425) (thanks @IceTank)
* [Add command gh workflow allowing to use release command in comments (#66)](https://github.com/PrismarineJS/prismarine-entity/commit/4dffa63e3dd45b8f3a42575a2f6f3c2fa47d1d50) (thanks @rom1504)
* [Update to node 18.0.0 (#65)](https://github.com/PrismarineJS/prismarine-entity/commit/7fe14b95f82089b27e20f12a14f709bc8bd5c206) (thanks @rom1504)
* [Bump @types/node from 18.16.13 to 20.2.1 (#64)](https://github.com/PrismarineJS/prismarine-entity/commit/887737f531d89b25e045c4f0db4ec66497eba9f8) (thanks @dependabot[bot])
* [Add missing type (#55)](https://github.com/PrismarineJS/prismarine-entity/commit/87a94dbaf698497f56968efbb396c3692431ae6f) (thanks @sefirosweb)
* [deprecate objectType and mobType (#53)](https://github.com/PrismarineJS/prismarine-entity/commit/e3aadc7e51dccc645d81825aa0bd40b3be88cb05) (thanks @Epirito)
* [Update package.json (#52)](https://github.com/PrismarineJS/prismarine-entity/commit/1156c9b9ae76b3e82ea57348c0f4e0cbdcb6216a) (thanks @Epirito)

### 2.2.0

* mcData to registry refactoring (step towards #2450)

### 2.1.1

* Update mcdata

### 2.1.0

* Adds Entity#getDroppedItem

### 2.0.0

* require mcversion in constructor
* add Entity#getCustomName()
* Add attributes for entity entity collision calculation (thanks @O-of)

### 1.2.0

* Add food saturation to typings
* Add id to typings
* Add effects to typings

### 1.1.0

* Added entity width property

### 1.0.0

* typescript definitions (thanks @IdanHo)

### 0.2.0

* extend EventEmitter

### 0.1.0

* Import from mineflayer
