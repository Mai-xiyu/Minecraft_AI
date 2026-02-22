## History

### 1.11.0
* [Bump mocha from 10.8.2 to 11.0.1 (#116)](https://github.com/PrismarineJS/prismarine-chat/commit/0168f676fe890b3cd5fc5d22502138c215cf72eb) (thanks @dependabot[bot])
* [fix toHTML length check](https://github.com/PrismarineJS/prismarine-chat/commit/17fe55e16e53b1010e3e6c5ccaa14c0f9441e259) (thanks @extremeheat)

### 1.10.1
* [Handle big and deep messages (#107)](https://github.com/PrismarineJS/prismarine-chat/commit/c990ba8017ab7d79738d54281d7355da0b5ac235) (thanks @extremeheat)

### 1.10.0
* [1.20.3 nbt chat handling (#103)](https://github.com/PrismarineJS/prismarine-chat/commit/1066a76e719c6cfd8c7596ddb3b9d9e624eac413) (thanks @extremeheat)

### 1.9.1
* [use Object.prototype.hasOwnProperty.call instead of Object.hasOwn (#101)](https://github.com/PrismarineJS/prismarine-chat/commit/3d8b67e1adcaed0c17059d42c02ad645d390b27f) (thanks @extremeheat)

### 1.9.0
* [Fix unsafe object lookups (#99)](https://github.com/PrismarineJS/prismarine-chat/commit/4536dca23b18b4cc6cbd825ca17e3adbb347cce9) (thanks @extremeheat)
* [Add command gh workflow allowing to use release command in comments (#98)](https://github.com/PrismarineJS/prismarine-chat/commit/494315fb9d022c83b4041f0ad7f828909fe7ccd0) (thanks @rom1504)
* [Update to node 18 (#96)](https://github.com/PrismarineJS/prismarine-chat/commit/bc28fe1aeed8246376b3ff720ee9658a29604a14) (thanks @rom1504)
* [Fix potential issue in toHTML (#95)](https://github.com/PrismarineJS/prismarine-chat/commit/d9a5bc8346291d51dcbe0fd4d3dc612ac741ad50) (thanks @extremeheat)
* [Add html generator (#94)](https://github.com/PrismarineJS/prismarine-chat/commit/1f19bccbec588b73b0546e783b1e90e11c52be5f) (thanks @extremeheat)

### 1.8.0

* Better translation handling (@ChipmunkMC)
* Allow specifying which ANSI formatting codes to use (@GhqstMC)
* Added a missing type in the loader (@Jarco-dev)

### 1.7.2

* Fix broken type definitions (@IceTank) [#81](https://github.com/PrismarineJS/prismarine-chat/pull/81)

### 1.7.1

* Fix release 

### 1.7.0

* Support 1.19 client side message formatting (@extremeheat)
* Fix motd color codes bleeding through their with block (@U9g)

### 1.6.1

* Update mcdata

### 1.6.0

* Added number type to getText()'s idx argument
* Remove resets on empty strings

### 1.5.0

* allow ChatMessage constructor to accept strings with legacy color codes (§) be converted to new json

### 1.4.1
* Remake ChatMessage#clone (@u9g)

### 1.4.0
* Add a example (@u9g)
* Add hex color code support (@U5B)
* use rest arg to allow many withs or extras (@u9g)
* Add missing json attribute to typescript defintions (@Paulomart & @u9g)

### 1.3.3
* fix typings

### 1.3.2
* Properly export loader function and export ChatMessage & MessageBuilder as types

### 1.3.1
* export ChatMessage object in typings

### 1.3.0
* add typings (@Gjum)

### 1.2.0
* Added fromNotch() (@u9g)
* Add support for array chat messages (@mat-1)

### 1.1.0
* Added MessageBuilder (@u9g)

### 1.0.4

* Added clone() and append() (@builder-247)
* update mojangson to 2.0.0 (@u9g)
* Add trailing color reset to .toAnsi() (@DrMoraschi)

### 1.0.3

* by default hide warnings

### 1.0.2

* ignore mojangson parsing error

### 1.0.1

* make lang option in toAnsi optional

### 1.0.0

* initial implementation
* extracted from mineflayer
