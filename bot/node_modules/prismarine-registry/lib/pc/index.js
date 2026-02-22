const nbt = require('prismarine-nbt')

const { networkBiomesToMcDataSchema, mcDataSchemaToNetworkBiomes } = require('./transforms')

module.exports = (data, staticData) => {
  let hasDynamicDimensionData = false

  return {
    loadDimensionCodec (codec) {
      const handlers = {
        chat_type (chat) {
          data.chatFormattingById = {}
          data.chatFormattingByName = {}
          for (const chatType of chat) {
            const d = chatType.element?.chat?.decoration ?? chatType.element?.chat
            if (!d) continue
            const n = {
              id: chatType.id,
              name: chatType.name,
              formatString: staticData.language[d.translation_key] || d.translation_key /* chat type minecraft:raw has the formatString given directly by the translation key */,
              parameters: d.parameters
            }
            if (staticData.supportFeature('incrementedChatType')) {
              // 1.21 - Player chat packet chat type now starts at 1
              data.chatFormattingById[chatType.id + 1] = n
            } else {
              data.chatFormattingById[chatType.id] = n
            }
            data.chatFormattingByName[chatType.name] = n
          }
        },
        dimension_type (dimensions) {
          data.dimensionsById = {}
          data.dimensionsByName = {}
          data.dimensionsArray = []

          for (const { name, id, element } of dimensions) {
            const n = name.replace('minecraft:', '')
            const d = {
              name: n,
              minY: element.min_y,
              height: element.height
            }
            data.dimensionsById[id] = d
            data.dimensionsByName[n] = d
            data.dimensionsArray.push(d)
          }
        },
        'worldgen/biome' (biomes) {
          data.biomes = []
          data.biomesByName = {}
          data.biomesArray = []

          biomes.map(e => networkBiomesToMcDataSchema(e, staticData))

          const allBiomes = []
          for (const { name, id, element } of biomes) {
            data.biomes[id] = element
            data.biomesByName[name] = element
            allBiomes.push(element)
          }
          data.biomesArray = allBiomes

          hasDynamicDimensionData = true
        }
      }

      if (staticData.supportFeature('segmentedRegistryCodecData')) {
        // 1.20.5+ - dimension data is now seperated outside the NBT and is sent through
        // multiple registry_data { id: registryName, entries: [key, registryData] } packets...
        const entries = codec.entries.map((e, ix) => ({ id: ix, name: e.key, element: nbt.simplify(e.value) }))
        handlers[codec.id.replace('minecraft:', '')]?.(entries)
      } else {
        const dimensionCodec = nbt.simplify(codec)
        for (const codecName in dimensionCodec) {
          handlers[codecName.replace('minecraft:', '')]?.(dimensionCodec[codecName].value)
        }
      }
    },

    writeDimensionCodec () {
      const codec = {}

      if (data.version['<']('1.16')) {
        return codec // no dimension codec in 1.15
      } else if (data.version['<']('1.16.2')) {
        return staticData.loginPacket.dimensionCodec
      } else if (data.version['<']('1.20.5')) {
        // Keep the old dimension codec data if it exists (re-encoding)
        // We don't have this data statically, should probably be added to mcData

        if (data.dimensionsArray) {
          codec['minecraft:dimension_type'] = nbt.comp({
            type: nbt.string('minecraft:dimension_type'),
            value: nbt.list(nbt.comp(
              data.dimensionsArray.map(dimension => ({
                name: dimension.name,
                id: dimension.id,
                element: {
                  min_y: dimension.minY
                }
              }))
            ))
          })
        } else {
          codec['minecraft:dimension_type'] = staticData.loginPacket.dimensionCodec.value['minecraft:dimension_type']
        }

        // if we have dynamic biome data (re-encoding), we can count on biome.effects
        // being in place. Otherwise, we need to use static data exclusively, e.g. flying squid.
        codec['minecraft:worldgen/biome'] = nbt.comp({
          type: nbt.string('minecraft:worldgen/biome'),
          value: nbt.list(nbt.comp(mcDataSchemaToNetworkBiomes(hasDynamicDimensionData ? data.biomesArray : null, staticData)))
        })
        // 1.19
        codec['minecraft:chat_type'] = staticData.loginPacket.dimensionCodec?.value?.['minecraft:chat_type']
        // NBT
        return nbt.comp(codec)
      } else {
        if (data.dimensionsArray) {
          codec['minecraft:dimension_type'] = {
            id: 'minecraft:dimension_type',
            entries: data.dimensionsArray.map(dimension => ({
              key: dimension.name,
              value: nbt.comp({
                min_y: dimension.minY
              })
            }))
          }
        } else {
          codec['minecraft:dimension_type'] = staticData.loginPacket.dimensionCodec['minecraft:dimension_type']
        }
        // if we have dynamic biome data (re-encoding), we can count on biome.effects
        // being in place. Otherwise, we need to use static data exclusively, e.g. flying squid.
        codec['minecraft:worldgen/biome'] = {
          id: 'minecraft:worldgen/biome',
          entries: nbt.comp(mcDataSchemaToNetworkBiomes(hasDynamicDimensionData ? data.biomesArray : null, staticData))
        }
        // 1.19
        codec['minecraft:chat_type'] = staticData.loginPacket.dimensionCodec?.['minecraft:chat_type']
        // No NBT at root anymore
        return codec
      }
    }
  }
}
