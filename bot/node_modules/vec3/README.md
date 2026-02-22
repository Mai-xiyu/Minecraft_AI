# vec3
[![NPM version](https://img.shields.io/npm/v/vec3.svg)](http://npmjs.com/package/vec3)
[![Build Status](https://github.com/PrismarineJS/node-vec3/workflows/CI/badge.svg)](https://github.com/PrismarineJS/node-vec3/actions?query=workflow%3A%22CI%22)

3D vector math with robust unit tests.

## Usage

```js
var v = require('vec3');

var v1 = v(1, 2, 3);
console.log(v1); // prints "(1, 2, 3)"
var v2 = v1.offset(0, 0, 1);
console.log(v2); // prints "(1, 2, 4)"
```

Or:

```js
var Vec3 = require('vec3').Vec3;

var v1 = new Vec3(1, 2, 3);
// etc...
```

More available functions are listed below in Test Coverage.

## Test Coverage

```
  v()
    ✔ no args
    ✔ x, y, z
    ✔ array
    ✔ object
    ✔ string coords
    ✔ deserialize
    ✔ invalid deserialize

  vec3
    ✔ isZero
    ✔ at
    ✔ xz
    ✔ xy
    ✔ yz
    ✔ xzy
    ✔ rounded
    ✔ round
    ✔ floored
    ✔ floor
    ✔ offset
    ✔ translate
    ✔ plus
    ✔ minus
    ✔ scaled
    ✔ abs
    ✔ distanceTo
    ✔ distanceSquared
    ✔ equals
    ✔ toString
    ✔ clone
    ✔ add
    ✔ subtract
    ✔ multiply
    ✔ divide
    ✔ set
    ✔ modulus
    ✔ volume
    ✔ min
    ✔ max
    ✔ update
    ✔ norm
    ✔ dot
    ✔ cross
    ✔ unit
    ✔ normalize
    ✔ scale
    ✔ xyDistanceTo
    ✔ xzDistanceTo
    ✔ yzDistanceTo
    ✔ innerProduct
    ✔ manhattanDistanceTo
    ✔ toArray

  50 passing (14ms)
```

More functions welcome in the form of pull requests.

## History

See [History](HISTORY.md)
