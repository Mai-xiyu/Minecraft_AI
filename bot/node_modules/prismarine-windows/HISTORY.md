### 2.9.0
* [Add Crafter into windows list for 1.20.3+ (#105)](https://github.com/PrismarineJS/prismarine-windows/commit/e081bc34c8282ef2a380e3f09d5f57f19703fab7) (thanks @wgaylord)

### 2.8.0
* [Export changedSlots computation to mineflayer (#102)](https://github.com/PrismarineJS/prismarine-windows/commit/98c3d66ae6aca733bb234d487686e2e534d1924d) (thanks @kaduvert)
* [Ensure numberClick with same slots doesn't do anything (#103)](https://github.com/PrismarineJS/prismarine-windows/commit/50e6bfbdb9c3bc26f06ea45760527b2da53eb1f3) (thanks @kaduvert)
* [Fix broken behaviour with craftingResultSlots (#101)](https://github.com/PrismarineJS/prismarine-windows/commit/51cc06e0f7dd39ddbb617962dfc1bb659fc172ce) (thanks @kaduvert)

### 2.7.0
* [More click modes (with tests!) (#74)](https://github.com/PrismarineJS/prismarine-windows/commit/9f19fb357b2a96e09060fa5c2393b9041cc869fe) (thanks @kaduvert)
* [Add command gh workflow allowing to use release command in comments (#98)](https://github.com/PrismarineJS/prismarine-windows/commit/6ddc90092d63f3838136d83e583d7c1d7ace3ae2) (thanks @rom1504)
* [fix](https://github.com/PrismarineJS/prismarine-windows/commit/8ab955e465ce9586bfba0286ef1340b86dc914e4) (thanks @rom1504)
* [Update to node 18.0.0 (#96)](https://github.com/PrismarineJS/prismarine-windows/commit/98912036737aa4c2e2f743b12bdb66eac5073889) (thanks @rom1504)
* [Bump @types/node from 18.16.13 to 20.2.1 (#95)](https://github.com/PrismarineJS/prismarine-windows/commit/cf7401e3caf1ff2a5f582338b3815eb1f80187b2) (thanks @dependabot[bot])
* [Fix slot layout for dispencer and droppers (#86)](https://github.com/PrismarineJS/prismarine-windows/commit/b42576a0e3eac7b42c843fa96c80191218efe97a) (thanks @IceTank)
* [Change slots from Array<Item> to Array<Item | null> (#85)](https://github.com/PrismarineJS/prismarine-windows/commit/652cd992b27254dcc7173e93ec8a112fd56cb459) (thanks @yurei-dll)
* [use registry.supportFeature (#82)](https://github.com/PrismarineJS/prismarine-windows/commit/3d4514ab56274cfe1fc5d578e3e101d6e41391f7) (thanks @Epirito)
* [Bump typed-emitter from 1.4.0 to 2.1.0 (#76)](https://github.com/PrismarineJS/prismarine-windows/commit/86e6aa0727c7e6a4ffa0602bf1aba7fd9d70f71f) (thanks @dependabot[bot])

## 2.6.1

* fix typo

## 2.6.0

* mcData to registry refactoring + anticipation of feature check refactoring

## 2.5.0

* Extend the events used for  windows

## 2.4.4
* update mcdata

## 2.4.3
* fixed typescript typings

## 2.4.2
* Fixed Exporting correctly and better window typings (#49)

### 2.4.1
* revert avoid emitting references

### 2.4.0

* fix bug with emitting null items (@imharvol)
* add typings to containerType
* fix slot count for generic 3x3 containers

### 2.3.0

* Click API endpoints returns changedSlots array (@nickelpro)

### 2.2.1

* Avoid emitting references (@imharvol)

### 2.2.0

* make nbt the fifth parameter of finditemrange (thanks @U9G)

### 2.1.0

* Add clear function (thanks @U9G)

### 2.0.0

* Fix 1.16 wrong ids, add utility functions
* BREAKING: update event changed from `windowUpdate` to `updateSlot`

### 1.6.0

* Add ability to find items by name (thanks @Naomi)

### 1.5.0

* 1.16.0 compat (thanks @DrakoTrogdor)

### 1.4.0

* typescript definitions (thanks @IdanHo)

### 1.3.0

* 1.15 support

### 1.2.0

bunch of changes by Karang :
* refactored
* more windows for both 1.14 and before

### 1.1.1

* fix for tossed item when crafted (thanks @karang)

### 1.1.0

* added support for villager trading windows (thanks @plexigras)

### 1.0.1

* bump mcdata

### 1.0.0

* bump dependencies

### 0.0.0

* Import from mineflayer
