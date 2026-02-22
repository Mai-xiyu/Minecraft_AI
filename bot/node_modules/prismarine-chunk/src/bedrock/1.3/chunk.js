const { ChunkVersion } = require('../common/constants')
const ChunkColumn = require('./ChunkColumn')

module.exports = (version) => {
  // Require once here to avoid requiring() on every new chunk instance
  const registry = version.blockRegistry || version
  const Block = require('prismarine-block')(registry)
  const Biome = require('prismarine-biome')(registry)
  return class Chunk extends ChunkColumn {
    constructor (options) {
      super(options, registry, Block, Biome)
      this.chunkVersion = this.chunkVersion || ChunkVersion.v1_16_0
      this.subChunkVersion = 8
    }

    static fromJson (str) {
      return new this(JSON.parse(str))
    }
  }
}
