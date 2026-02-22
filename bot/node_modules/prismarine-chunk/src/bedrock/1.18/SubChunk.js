const SubChunk13 = require('../1.3/SubChunk')
const { StorageType } = require('../common/constants')
const PalettedStorage = require('../common/PalettedStorage')

class SubChunk118 extends SubChunk13 {
  loadRuntimePalette (storageLayer, stream, paletteSize) {
    this.palette[storageLayer] = []

    for (let i = 0; i < paletteSize; i++) {
      const runtimeId = stream.readZigZagVarInt()
      const block = this.registry.blocksByRuntimeId[runtimeId]
      this.palette[storageLayer][i] = { stateId: block.stateId, ...block, count: 0 }
    }
  }

  loadPalettedBlocks (storageLayer, stream, bitsPerBlock, format) {
    if ((format === StorageType.Runtime) && (bitsPerBlock === 0)) {
      this.palette[storageLayer] = []
      this.blocks[storageLayer] = new PalettedStorage(1)
      const stateId = stream.readVarInt() >> 1
      this.addToPalette(storageLayer, stateId)
      return
    }
    return super.loadPalettedBlocks(...arguments)
  }

  writeStorage (stream, storageLayer, format) {
    if ((format === StorageType.Runtime) && (this.palette[storageLayer].length === 1)) {
      stream.writeUInt8(1) // palette type
      stream.writeZigZagVarInt(this.palette[storageLayer][0].stateId)
      return
    }

    return super.writeStorage(...arguments)
  }
}

module.exports = SubChunk118
