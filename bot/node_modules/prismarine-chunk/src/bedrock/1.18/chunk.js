const { ChunkVersion } = require('../common/constants')
const ChunkColumn = require('./ChunkColumn')

module.exports = (version) => {
  const registry = version.blockRegistry || version
  const Block = require('prismarine-block')(registry)
  const Biome = require('prismarine-biome')(registry)
  return class Chunk extends ChunkColumn {
    constructor (options) {
      super(options, registry, Block, Biome)
      this.chunkVersion = this.chunkVersion || ChunkVersion.v1_18_0
      this.subChunkVersion = 9
    }

    static fromJson (str) {
      return new this(JSON.parse(str))
    }
  }
}
