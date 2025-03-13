## History

### 1.38.1
* [Fix pc1.18 light index (#271)](https://github.com/PrismarineJS/prismarine-chunk/commit/9a9673b8a7e4b4810dd128febf25467bf2b99b85) (thanks @extremeheat)

### 1.38.0
* [Support for hashed block network ID's (#237)](https://github.com/PrismarineJS/prismarine-chunk/commit/f1c1f9a7d4cf977ce46975503f8f92db7836e8c9) (thanks @FreezeEngine)

### 1.37.0
* [Bump mocha from 10.8.2 to 11.0.1 (#266)](https://github.com/PrismarineJS/prismarine-chunk/commit/ccd97e55d4e60db9f70c093e507ff69598eb3f43) (thanks @dependabot[bot])
* [pc1.18+: Fix world height defaults and light masks (#267)](https://github.com/PrismarineJS/prismarine-chunk/commit/92ae1d347299a9925a23d97014ece07c98627fd0) (thanks @extremeheat)

### 1.36.0
* [1.21 (#263)](https://github.com/PrismarineJS/prismarine-chunk/commit/381497b893857a0c60836873f3c26f8efc52f29b) (thanks @Madlykeanu)
* [Bump @types/node from 20.16.11 to 22.7.5 (#262)](https://github.com/PrismarineJS/prismarine-chunk/commit/4cc2384fb49aba138644f2ef5b35cef07e56f6eb) (thanks @dependabot[bot])
* [Update index.d.ts](https://github.com/PrismarineJS/prismarine-chunk/commit/2dc9a9d467810c906b132595567b05d8f58b7bed) (thanks @extremeheat)
* [Minor fix loadParsedLights type (#239)](https://github.com/PrismarineJS/prismarine-chunk/commit/18d786e31ab3f4f7c3f61058e08e9e421feecfd2) (thanks @zardoy)
* [fix: toJson / fromJson didn't use maxBitsPerBlock (#238)](https://github.com/PrismarineJS/prismarine-chunk/commit/eb39a905761a36f733a456110e6b49d655bf5c16) (thanks @zardoy)
* [use features in tests (#233)](https://github.com/PrismarineJS/prismarine-chunk/commit/0631db23c79f63d0bd37cb2764a9d6364c95688c) (thanks @extremeheat)

### 1.35.0
* [Fix direct palettes (#232)](https://github.com/PrismarineJS/prismarine-chunk/commit/6422abc93ac121f635a03ffa339feb6e5b7b37bf) (thanks @frej4189)
* [Fixes issue https://github.com/PrismarineJS/prismarine-chunk/issues/229 (#231)](https://github.com/PrismarineJS/prismarine-chunk/commit/bed78672ba07cb6d82ee66d148f8ce0ae1ce83c2) (thanks @Flonja)
* [Add command gh workflow allowing to use release command in comments (#228)](https://github.com/PrismarineJS/prismarine-chunk/commit/0ac8714df114707d8f9c1d92fc0a7b5dcfcce619) (thanks @rom1504)

## 1.34.0

* 1.20 support

## 1.33.1
* Fix attempting to set skylight in chunks with no skylight

## 1.33.0
* Bedrock 1.19.1 support, fix pc 1.18 world height from disk

## 1.32.0

* 1.19 support

## 1.31.0

* update mcdata

## 1.30.0

* Bedrock 1.16 - 1.18.0 chunks (@extremeheat)
* Block sections are not biomes (@nickelpro)

## 1.29.0

* Implement prismarine-registry, basic block entities and 1.18 disk loading

## 1.28.1

* improve the palette hack for 1.18

## 1.28.0

* expose palette in 1.18

## 1.27.0

* Add 1.18 chunk support (@nickelpro)

## 1.26.0

* Fix fromLongArray index bug (@nickelpro)
* Fix bitArray Or bug (@nickelpro)
* Correctly update empty light sections (@nickelpro)
* Be more correct about updating light masks (@nickelpro)
* Add BitArray.or test (@nickelpro)

## 1.25.0

* Add type info and bounds checks (@nickelpro)
* Fix skyLightMask bookkeeping (@nickelpro)
* Set GLOBAL_BITS_PER_BLOCK to 16 (@nickelpro)
* Expose ChunkSections (@extremeheat)

## 1.24.0

* 1.17 support (thanks @nickelpro @Archengius @u9g)

## 1.23.0

* Add toArray/fromArray to BitArrays (@Karang)
* Use Uint32Array instead of Array (@Saiv46)
* add version property to chunk object (@u9g)
* Fix pe -> bedrock (@nickelpro)

## 1.22.0

* optimize for browser by inlining getSectionIndex and removing asserts (@rom1504)

## 1.21.0

* fix initialize in all versions but 1.8 (@rom1504)
* add typescript typings (@Darkflame72)

## 1.20.3

* Several bug fix (thanks @IdanHo)

## 1.20.2

* Discard the 0 length of the missing palette array in 1.9 (thanks @IdanHo)

## 1.20.1

* Return air when reading y < 0 or y >= 256

## 1.20.0

* 1.16 support

## 1.19.0

* setBlockData for 1.13, 1.14, 1.15 (thanks @Deudly)

## 1.18.1

* fix bitwise unsigned operators => fix dumping chunks for 1.9->1.12

## 1.18.0

* reimplement 1.9->1.12 in a similar way to 1.13 (remove protodef dependency)
* implement full chunk for 1.8
* add empty load and dump biomes and light methods for simplicity in all versions

## 1.17.0

* support for full chunk property (thanks @Karang)
* fix bug in json serialization

## 1.16.0

* support for 1.15 chunk (thanks @Karang)

## 1.15.0

* support for 1.14 chunk (thanks @Karang)

## 1.14.0

* faster 1.13 chunk implementation (thanks @Karang)

## 1.13.0

* fast json serialization/parsing for out of process loading/writing

## 1.12.0

* 1.13 support (thanks @hornta)

## 1.11.1

* fix dumping for noSkylight chunks for 1.9-1.12 (thanks @IdanHo)

## 1.11.0

* add chunk handling for chunks without skylight data in 1.8 (thanks @skullteria)

## 1.10.0

* support 1.13
* better tests

## 1.9.1

* standardjs
* circleci 2
* better no chunk implementation exception

## 1.9.0

* small 1.9 fix (thanks @Flynnn)
* handle skylightsent in 1.8

## 1.8.2

* fix initialize in 1.8 + test

### 1.8.1

* fix initialize in 1.8

### 1.8.0

* optimization of 1.9 chunk done by @allain

### 1.7.0

* supports mcpc 1.12 (same as 1.9)

### 1.6.0

* add skyLightSent to load

### 1.5.1

* use last protodef, fix longToByte (no countTypeArgs), and remove gulp

### 1.5.0

* supports mcpc 1.10 and 1.11 (same as 1.9)

### 1.4.0

* supports mcpc 1.9 (thanks @Flynnn)

### 1.3.0

* supports bitmap in load and dump in 1.8, default to bitmap == 0xFFFF

### 1.2.0

* support MCPE 1.0 chunks

### 1.1.0

* support MCPE 0.14 chunks

### 1.0.1

* update to babel6

### 1.0.0

* bump dependencies

### 0.3.2

* simplify and fix initialize

### 0.3.1

* fix iniPos in initialize

### 0.3.0

* add Chunk.initialize, useful for fast generation

### 0.2.1

 * fix the badge

### 0.2.0

 * use vec3
 * add an example + doc
 * use prismarine-block

### 0.1.0

* First version, basic functionality
