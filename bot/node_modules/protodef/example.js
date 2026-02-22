const assert = require('assert')
const ProtoDef = require('protodef').ProtoDef
const Serializer = require('protodef').Serializer
const Parser = require('protodef').Parser

BigInt.prototype.toJSON = function () { // eslint-disable-line -- Allow serializing BigIntegers
  return this.toString()
}

// the protocol can be in a separate json file
const exampleProtocol = {
  container: 'native',
  varint: 'native',
  byte: 'native',
  bool: 'native',
  switch: 'native',
  bitflags: 'native',
  entity_look: [
    'container',
    [
      {
        name: 'entityId',
        type: 'varint'
      },
      {
        name: 'yaw',
        type: 'i8'
      },
      {
        name: 'pitch',
        type: 'i8'
      },
      { name: 'flags', type: ['bitflags', { type: 'u8', flags: ['onGround'] }] },
      { name: 'longId', type: 'varint64' },
      { name: 'longerId', type: 'varint128' },
      { name: 'zigzagId', type: 'zigzag32' },
      { name: 'zigzagBig', type: 'zigzag64' }
    ]
  ],
  packet: [
    'container',
    [
      {
        name: 'name',
        type: [
          'mapper',
          {
            type: 'varint',
            mappings: {
              22: 'entity_look'
            }
          }
        ]
      },
      {
        name: 'params',
        type: [
          'switch',
          {
            compareTo: 'name',
            fields: {
              entity_look: 'entity_look'
            }
          }
        ]
      }
    ]
  ]
}

const proto = new ProtoDef()
proto.addTypes(exampleProtocol)
const parser = new Parser(proto, 'packet')
const serializer = new Serializer(proto, 'packet')

serializer.write({
  name: 'entity_look',
  params: {
    entityId: 1,
    yaw: 1,
    pitch: 6,
    flags: {
      onGround: true
    },
    longId: 13n,
    longerId: 2n ** 68n, // 9 bytes integer, 10 over wire
    zigzagId: -3,
    zigzagBig: 4294967296n
  }
})
serializer.pipe(parser)

parser.on('data', function (chunk) {
  console.dir(chunk, { depth: null })
  assert.deepEqual([...chunk.buffer], [22, 1, 1, 6, 1, 13, 128, 128, 128, 128, 128, 128, 128, 128, 128, 32, 5, 128, 128, 128, 128, 32])
})
