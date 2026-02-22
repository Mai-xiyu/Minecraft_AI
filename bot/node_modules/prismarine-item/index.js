const nbt = require('prismarine-nbt')

function loader (registryOrVersion) {
  const registry = typeof registryOrVersion === 'string' ? require('prismarine-registry')(registryOrVersion) : registryOrVersion
  class Item {
    constructor (type, count, metadata, nbt, stackId, sentByServer) {
      if (type == null) return

      if (metadata instanceof Object) {
        sentByServer = stackId
        stackId = nbt
        nbt = metadata
        metadata = 0
      }

      this.type = type
      this.count = count
      this.metadata = metadata == null ? 0 : metadata
      this.nbt = nbt || null

      // pc 1.20.5, TODO: properly implement...
      if (registry.supportFeature('itemsWithComponents')) {
        this.components = []
        this.removedComponents = []
        this.componentMap = new Map() // Pf146
      }

      // Probably add a new feature to mcdata, e.g itemsCanHaveStackId
      if (registry.type === 'bedrock') {
        if (stackId == null && !sentByServer) stackId = Item.nextStackId()
        this.stackId = stackId
      } else {
        this.stackId = null
      }

      const itemEnum = registry.items[type]
      if (itemEnum) {
        this.name = itemEnum.name
        this.displayName = itemEnum.displayName
        this.stackSize = itemEnum.stackSize
        this.maxDurability = itemEnum.maxDurability

        if ('variations' in itemEnum) {
          const variation = itemEnum.variations.find((item) => item.metadata === metadata)
          if (variation) this.displayName = variation.displayName
        }

        // Can't initialize fields if the item was sent by the server
        if (!sentByServer) {
          // The 'itemEnum.maxDurability' checks to see if this item can lose durability
          if (registry.supportFeature('explicitMaxDurability') && this.maxDurability && !this.durabilityUsed) this.durabilityUsed = 0
        }
      } else {
        this.name = 'unknown'
        this.displayName = 'unknown'
        this.stackSize = 1
      }
    }

    static equal (item1, item2, matchStackSize = true, matchNbt = true) {
      if (item1 == null && item2 == null) {
        return true
      } else if (item1 == null) {
        return false
      } else if (item2 == null) {
        return false
      } else {
        return (
          item1.type === item2.type &&
          item1.metadata === item2.metadata &&
          (matchStackSize ? item1.count === item2.count : true) &&
          (matchNbt ? JSON.stringify(item1.nbt) === JSON.stringify(item2.nbt) : true)
        )
      }
    }

    // TODO: Move stack ID handling to prismarine-registry, as calling the loader again resets it here
    static currentStackId = 0
    static nextStackId () {
      return Item.currentStackId++
    }

    static toNotch (item, serverAuthoritative = true) {
      const hasNBT = item && item.nbt && Object.keys(item.nbt.value).length > 0

      if (registry.type === 'pc') {
        if (registry.supportFeature('itemsWithComponents')) {
          if (!item) return { itemCount: 0 }
          return {
            itemCount: item.count,
            itemId: item.type,
            addedComponentCount: item.components.length,
            removedComponentCount: item.removedComponents.length,
            components: item.components,
            removeComponents: item.removedComponents
          }
        } else if (registry.supportFeature('itemSerializationAllowsPresent')) {
          if (item == null) return { present: false }
          return {
            present: true,
            itemId: item.type,
            itemCount: item.count,
            nbtData: hasNBT ? item.nbt : undefined
          }
        } else if (registry.supportFeature('itemSerializationUsesBlockId')) {
          if (item == null) return { blockId: -1 }
          return {
            blockId: item.type,
            itemCount: item.count,
            itemDamage: item.metadata,
            nbtData: hasNBT ? item.nbt : undefined
          }
        }
      } else if (registry.type === 'bedrock') {
        if (item == null || item.type === 0) return { network_id: 0 }

        if (registry.supportFeature('itemSerializeUsesAuxValue')) {
          return {
            network_id: item.id,
            auxiliary_value: (item.metadata << 8) | (item.count & 0xff),
            can_place_on: item.blocksCanPlaceOn,
            can_destroy: item.blocksCanDestroy,
            blocking_tick: 0,
            has_nbt: hasNBT,
            nbt: hasNBT ? { version: 1, nbt: item.nbt } : undefined
          }
        } else {
          return {
            network_id: item.type,
            count: item.count,
            metadata: item.metadata,
            has_stack_id: serverAuthoritative,
            stack_id: serverAuthoritative ? item.stackId : undefined,
            block_runtime_id: 0,
            extra: {
              can_place_on: item.blocksCanPlaceOn,
              can_destroy: item.blocksCanDestroy,
              blocking_tick: 0,
              has_nbt: hasNBT,
              nbt: hasNBT ? { version: 1, nbt: item.nbt } : undefined
            }
          }
        }
      }
      throw new Error("Don't know how to serialize for this mc version ")
    }

    static fromNotch (networkItem, stackId) {
      if (registry.type === 'pc') {
        if (registry.supportFeature('itemsWithComponents')) { // 1.20.5+
          if (networkItem.itemCount === 0) return null
          const item = new Item(networkItem.itemId, networkItem.itemCount, null, null, true)
          item.components = networkItem.components
          item.removedComponents = networkItem.removeComponents
          item.componentMap = new Map() // Pf146
          if (item.components) {
            for (const component of item.components) {
              item.componentMap.set(component.type, component)
            }
          }
          return item
        } else if (registry.supportFeature('itemSerializationWillOnlyUsePresent')) {
          if (networkItem.present === false) return null
          return new Item(networkItem.itemId, networkItem.itemCount, networkItem.nbtData, null, true)
        } else if (registry.supportFeature('itemSerializationAllowsPresent')) {
          if (networkItem.itemId === -1 || networkItem.present === false) return null
          return new Item(networkItem.itemId, networkItem.itemCount, networkItem.nbtData, null, true)
        } else if (registry.supportFeature('itemSerializationUsesBlockId')) {
          if (networkItem.blockId === -1) return null
          return new Item(networkItem.blockId, networkItem.itemCount, networkItem.itemDamage, networkItem.nbtData, null, true)
        } else {
          throw new Error('Unknown Minecraft item version')
        }
      } else if (registry.type === 'bedrock') {
        if (networkItem.network_id === 0) return null

        if (registry.supportFeature('itemSerializeUsesAuxValue')) {
          const item = new Item(networkItem.network_id, networkItem.auxiliary_value & 0xff, networkItem.auxiliary_value >> 8, networkItem.nbt?.nbt, stackId, true)
          if (networkItem.can_place_on.length > 0) item.blocksCanPlaceOn = networkItem.can_place_on
          if (networkItem.can_destroy.length > 0) item.blocksCanDestroy = networkItem.can_destroy
          return item
        } else {
          const item = new Item(networkItem.network_id, networkItem.count, networkItem.metadata, networkItem.extra.nbt?.nbt, networkItem.stack_id, true)
          if (networkItem.extra.can_place_on.length > 0) item.blocksCanPlaceOn = networkItem.extra.can_place_on
          if (networkItem.extra.can_destroy.length > 0) item.blocksCanDestroy = networkItem.extra.can_destroy
          return item
        }
      }
      throw new Error("Don't know how to deserialize for this mc version")
    }

    get customName () {
      return this?.nbt?.value?.display?.value?.Name?.value ?? null
    }

    set customName (newName) {
      if (!this.nbt) this.nbt = nbt.comp({})
      if (!this.nbt.value.display) this.nbt.value.display = { type: 'compound', value: {} }
      this.nbt.value.display.value.Name = nbt.string(newName)
    }

    get customLore () {
      if (!this.nbt?.value?.display) return null
      return nbt.simplify(this.nbt).display.Lore ?? null
    }

    set customLore (newLore) {
      if (!this.nbt) this.nbt = nbt.comp({})
      if (!this.nbt.value.display) this.nbt.value.display = { type: 'compound', value: {} }

      this.nbt.value.display.value.Lore = registry.supportFeature('itemLoreIsAString')
        ? nbt.string(newLore)
        : nbt.list(nbt.string(newLore))
    }

    // gets the cost based on previous anvil uses
    get repairCost () {
      return this?.nbt?.value?.RepairCost?.value ?? 0
    }

    set repairCost (newRepairCost) {
      if (!this?.nbt) this.nbt = nbt.comp({})

      this.nbt.value.RepairCost = nbt.int(newRepairCost)
    }

    get enchants () {
      if (Object.keys(this).length === 0) return []
      const enchantNbtKey = registry.supportFeature('nbtNameForEnchant')
      const typeOfEnchantLevelValue = registry.supportFeature('typeOfValueForEnchantLevel')
      const useStoredEnchantments = registry.supportFeature('booksUseStoredEnchantments') && this.name === 'enchanted_book'

      if (typeOfEnchantLevelValue === 'short' && enchantNbtKey === 'ench') {
        let itemEnch = []

        if (useStoredEnchantments && this?.nbt?.value?.StoredEnchantments) {
          itemEnch = nbt.simplify(this.nbt).StoredEnchantments
        } else if (this?.nbt?.value?.ench) {
          itemEnch = nbt.simplify(this.nbt).ench
        } else {
          itemEnch = []
        }

        return itemEnch.map((ench) => ({ lvl: ench.lvl, name: registry.enchantments[ench.id]?.name || null }))
      } else if (typeOfEnchantLevelValue === 'string' && enchantNbtKey === 'Enchantments') {
        let itemEnch = []

        if (useStoredEnchantments && this?.nbt?.value?.StoredEnchantments) {
          itemEnch = nbt.simplify(this.nbt).StoredEnchantments
        } else if (this?.nbt?.value?.Enchantments) {
          itemEnch = nbt.simplify(this.nbt).Enchantments
        } else {
          itemEnch = []
        }

        return itemEnch.map((ench) => ({
          lvl: ench.lvl,
          name: typeof ench.id === 'string' ? ench.id.replace('minecraft:', '') : null
        }))
      }
      throw new Error("Don't know how to get the enchants from an item on this mc version")
    }

    set enchants (normalizedEnchArray) {
      const enchListName = registry.supportFeature('nbtNameForEnchant')
      const type = registry.supportFeature('typeOfValueForEnchantLevel')
      if (!type) throw new Error("Don't know the serialized type for enchant level")

      const useStoredEnchants = this.name === 'enchanted_book' && registry.supportFeature('booksUseStoredEnchantments')

      const enchs = normalizedEnchArray.map(({ name, lvl }) => {
        const value =
          type === 'short'
            ? registry.enchantmentsByName[name].id
            : `minecraft:${registry.enchantmentsByName[name].name}`
        return { id: { type, value }, lvl: nbt.short(lvl) }
      })

      if (enchs.length !== 0) {
        if (!this.nbt) this.nbt = nbt.comp({})
        this.nbt.value[useStoredEnchants ? 'StoredEnchantments' : enchListName] = nbt.list(nbt.comp(enchs))
      } else if (this.enchants.length !== 0) {
        delete this.nbt?.[useStoredEnchants ? 'StoredEnchantments' : enchListName]
      }
    }

    get blocksCanPlaceOn () {
      const blockNames = this?.nbt?.value?.CanPlaceOn?.value?.value ?? []
      return blockNames.map(name => [name])
    }

    set blocksCanPlaceOn (newBlocks) {
      if (newBlocks.length === 0) {
        if (this.blocksCanPlaceOn.length !== 0) delete this.nbt.value.CanPlaceOn
        return
      }
      if (!this.nbt) this.nbt = nbt.comp({})

      const blockNames = []
      for (const block of newBlocks) {
        let [ns, name] = block.split(':')
        if (!name) {
          name = ns
          ns = 'minecraft'
        }
        blockNames.push(`${ns}:${name}`)
      }

      this.nbt.value.CanPlaceOn = nbt.list(nbt.string(blockNames))
    }

    get blocksCanDestroy () {
      const blockNames = this?.nbt?.value?.CanDestroy?.value?.value ?? []
      return blockNames.map(name => [name])
    }

    set blocksCanDestroy (newBlocks) {
      if (newBlocks.length === 0) {
        if (this.blocksCanDestroy.length !== 0) delete this.nbt.value.CanDestroy
        return
      }
      if (!this.nbt) this.nbt = nbt.comp({})

      const blockNames = []
      for (const block of newBlocks) {
        let [ns, name] = block.split(':')
        if (!name) {
          name = ns
          ns = 'minecraft'
        }
        blockNames.push(`${ns}:${name}`)
      }

      this.nbt.value.CanDestroy = nbt.list(nbt.string(blockNames))
    }

    get durabilityUsed () {
      const where = registry.supportFeature('whereDurabilityIsSerialized')
      let ret

      if (this.componentMap && this.componentMap.has('damage')) { // Pf146
        ret = this.componentMap.get('damage').data // Pdaf7
      }

      if (ret === undefined) {
        if (where === 'Damage') ret = this.nbt?.value?.Damage?.value
        else if (where === 'metadata') ret = this.metadata
        else throw new Error('unknown durability location')
      }

      return ret ?? (this.maxDurability ? 0 : null)
    }

    set durabilityUsed (value) {
      const where = registry.supportFeature('whereDurabilityIsSerialized')
      if (where === 'Damage') {
        if (!this?.nbt) this.nbt = nbt.comp({})
        this.nbt.value.Damage = nbt.int(value)
      } else if (where === 'metadata') {
        this.metadata = value
      } else {
        throw new Error("Don't know how to set item durability for this mc version")
      }
    }

    get spawnEggMobName () {
      if (registry.supportFeature('spawnEggsHaveSpawnedEntityInName')) {
        return this.name.replace('_spawn_egg', '')
      }

      if (registry.supportFeature('spawnEggsUseInternalIdInNbt')) {
        return registry.entitiesArray.find((o) => o.internalId === this.metadata).name
      }

      if (registry.supportFeature('spawnEggsUseEntityTagInNbt')) {
        const data = nbt.simplify(this.nbt)
        const entityName = data.EntityTag.id
        return entityName.replace('minecraft:', '')
      }

      throw new Error("Don't know how to get spawn egg mob name for this mc version")
    }
  }

  Item.anvil = require('./lib/anvil.js')(registry, Item)
  return Item
}

module.exports = loader
