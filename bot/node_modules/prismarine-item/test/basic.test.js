/* eslint-env mocha */

const expect = require('expect').default

describe('test based on examples', () => {
  describe('1.8 iron shovel', () => {
    const Item = require('prismarine-item')('1.8')
    const ironShovelItem = new Item(256, 1)

    it('constructor makes item correctly', () => {
      const val = { type: 256, count: 1, metadata: 0, nbt: null, name: 'iron_shovel', displayName: 'Iron Shovel', stackSize: 1, stackId: null, maxDurability: 250 }
      expect(JSON.parse(JSON.stringify(ironShovelItem))).toStrictEqual(val)
    })

    it('use .toNotch', () => {
      expect(Item.toNotch(ironShovelItem)).toStrictEqual({ blockId: 256, itemCount: 1, itemDamage: 0, nbtData: undefined })
    })

    it('use .fromNotch', () => {
      const toNotch = Item.toNotch(ironShovelItem)
      const fromNotch = Item.fromNotch(toNotch)
      const expectedObj = { count: 1, displayName: 'Iron Shovel', metadata: 0, name: 'iron_shovel', nbt: null, stackSize: 1, type: 256, stackId: null, maxDurability: 250 }
      expect(JSON.parse(JSON.stringify(fromNotch))).toStrictEqual(expectedObj)
    })
  })
  describe('1.13.2 iron shovel', () => {
    const Item = require('prismarine-item')('1.13.2')
    const ironShovelItem = new Item(472, 1)

    it('constructor makes item correctly', () => {
      const expectedObj = { count: 1, displayName: 'Iron Shovel', metadata: 0, name: 'iron_shovel', nbt: null, stackSize: 1, type: 472, stackId: null, maxDurability: 250 }
      expect(JSON.parse(JSON.stringify(ironShovelItem))).toStrictEqual(expectedObj)
    })

    it('use .toNotch', () => {
      const expectedObj = { itemCount: 1, itemId: 472, present: true, nbtData: undefined }
      expect(Item.toNotch(ironShovelItem)).toStrictEqual(expectedObj)
    })

    it('use .fromNotch', () => {
      const toNotch = Item.toNotch(ironShovelItem)
      const fromNotch = Item.fromNotch(toNotch)
      const expectedObj = { count: 1, displayName: 'Iron Shovel', metadata: 0, name: 'iron_shovel', nbt: null, stackSize: 1, type: 472, stackId: null, maxDurability: 250 }
      expect(JSON.parse(JSON.stringify(fromNotch))).toStrictEqual(expectedObj)
    })
  })
  describe('bedrock_1.19.1 iron shovel', () => {
    const registry = require('prismarine-registry')('bedrock_1.19.1')
    const Item = require('prismarine-item')(registry)
    const ironShovelItem = new Item(registry.itemsByName.iron_shovel.id, 1)

    it('constructor makes item correctly', () => {
      const val = { type: registry.itemsByName.iron_shovel.id, count: 1, metadata: 0, nbt: { name: '', type: 'compound', value: { Damage: { type: 'int', value: 0 } } }, name: 'iron_shovel', displayName: 'Iron Shovel', stackSize: 1, stackId: 0, maxDurability: 250 }
      expect(JSON.parse(JSON.stringify(ironShovelItem))).toStrictEqual(val)
    })

    it('use .toNotch', () => {
      expect(Item.toNotch(ironShovelItem)).toStrictEqual({ network_id: registry.itemsByName.iron_shovel.id, count: 1, metadata: 0, has_stack_id: true, stack_id: 0, block_runtime_id: 0, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { Damage: { type: 'int', value: 0 } } } }, can_place_on: [], can_destroy: [], blocking_tick: 0 } })
    })

    it('use .fromNotch', () => {
      const toNotch = Item.toNotch(ironShovelItem)
      const fromNotch = Item.fromNotch(toNotch)
      const expectedObj = { count: 1, displayName: 'Iron Shovel', metadata: 0, name: 'iron_shovel', nbt: { name: '', type: 'compound', value: { Damage: { type: 'int', value: 0 } } }, stackSize: 1, type: registry.itemsByName.iron_shovel.id, stackId: 0, maxDurability: 250 }
      expect(JSON.parse(JSON.stringify(fromNotch))).toStrictEqual(expectedObj)
    })
  })
})

describe('get Item.enchants', () => {
  describe('1.8.8 test', () => {
    const Item = require('prismarine-item')('1.8.8')

    it('diamond axe with fortune 2', () => {
      const item = Item.fromNotch({ blockId: 279, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 2 }, id: { type: 'short', value: 35 } }] } }, RepairCost: { type: 'int', value: 1 } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 2, name: 'fortune' }])
    })

    it('gold helmet with fire prot 3, aqua afin 1, unbr 2', () => {
      const item = Item.fromNotch({ blockId: 314, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 3 }, id: { type: 'short', value: 1 } }, { lvl: { type: 'short', value: 2 }, id: { type: 'short', value: 34 } }, { lvl: { type: 'short', value: 1 }, id: { type: 'short', value: 6 } }] } }, RepairCost: { type: 'int', value: 3 } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 3, name: 'fire_protection' }, { lvl: 2, name: 'unbreaking' }, { lvl: 1, name: 'aqua_affinity' }])
    })

    it('carrot on stick with unbr 1', () => {
      const item = Item.fromNotch({ blockId: 398, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 1 }, id: { type: 'short', value: 34 } }] } }, RepairCost: { type: 'int', value: 1 } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 1, name: 'unbreaking' }])
    })

    it('stone pick with eff 4', () => {
      const item = Item.fromNotch({ blockId: 274, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 4 }, id: { type: 'short', value: 32 } }] } }, RepairCost: { type: 'int', value: 1 } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 4, name: 'efficiency' }])
    })

    it('fishing rod with luck 3 lure 3', () => {
      const item = Item.fromNotch({ blockId: 346, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 3 }, id: { type: 'short', value: 61 } }, { lvl: { type: 'short', value: 3 }, id: { type: 'short', value: 62 } }] } }, RepairCost: { type: 'int', value: 3 } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 3, name: 'luck_of_the_sea' }, { lvl: 3, name: 'lure' }])
    })

    it('diamond sword (unenchanted)', () => {
      const item = Item.fromNotch({ blockId: 276, itemCount: 1, itemDamage: 0 })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([])
    })

    it('enchanted book rename', () => {
      const item = Item.fromNotch({ blockId: 403, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { StoredEnchantments: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 1 }, id: { type: 'short', value: 3 } }] } } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 1, name: 'blast_protection' }])
    })

    it('(64x) blocks rename', () => {
      const item = Item.fromNotch({ blockId: 1, itemCount: 64, itemDamage: 0 })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([])
    })
  })
  describe('1.12.2 test', () => {
    const Item = require('prismarine-item')('1.12.2')

    it('sharp 5 dia sword', () => {
      const item = Item.fromNotch({ blockId: 276, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 5 }, id: { type: 'short', value: 16 } }] } }, RepairCost: { type: 'int', value: 1 } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 5, name: 'sharpness' }])
    })
    it('mending 1 elytra', () => {
      const item = Item.fromNotch({ blockId: 443, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'int', value: 1 }, id: { type: 'int', value: 70 } }] } } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 1, name: 'mending' }])
    })
  })
  describe('1.16.5 test', () => {
    const Item = require('prismarine-item')('1.16.5')

    it('diamond sword (unenchanted)', () => {
      const item = Item.fromNotch({ present: true, itemId: 603, itemCount: 1, nbtData: { type: 'compound', name: '', value: { Damage: { type: 'int', value: 0 } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([])
    })
    it('iron shovel w/ eff2 for2 ub2', () => {
      const item = Item.fromNotch({ present: true, itemId: 600, itemCount: 1, nbtData: { type: 'compound', name: '', value: { RepairCost: { type: 'int', value: 3 }, Damage: { type: 'int', value: 0 }, Enchantments: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 2 }, id: { type: 'string', value: 'minecraft:efficiency' } }, { lvl: { type: 'short', value: 2 }, id: { type: 'string', value: 'minecraft:fortune' } }, { lvl: { type: 'short', value: 2 }, id: { type: 'string', value: 'minecraft:unbreaking' } }] } } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 2, name: 'efficiency' }, { lvl: 2, name: 'fortune' }, { lvl: 2, name: 'unbreaking' }])
    })
    it('ench book w/ resp1 blastprot 1', () => {
      const item = Item.fromNotch({ present: true, itemId: 848, itemCount: 1, nbtData: { type: 'compound', name: '', value: { StoredEnchantments: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 1 }, id: { type: 'string', value: 'minecraft:respiration' } }, { lvl: { type: 'short', value: 1 }, id: { type: 'string', value: 'minecraft:blast_protection' } }] } }, RepairCost: { type: 'int', value: 1 } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 1, name: 'respiration' }, { lvl: 1, name: 'blast_protection' }])
    })
    it('music disc', () => {
      const item = Item.fromNotch({ present: true, itemId: 911, itemCount: 1 })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([])
    })
    it('fishing rod w/ mending', () => {
      const item = Item.fromNotch({ present: true, itemId: 684, itemCount: 1, nbtData: { type: 'compound', name: '', value: { RepairCost: { type: 'int', value: 1 }, Damage: { type: 'int', value: 0 }, Enchantments: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 1 }, id: { type: 'string', value: 'minecraft:mending' } }] } } } } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 1, name: 'mending' }])
    })
  })
  describe('bedrock_1.17.10 test', () => {
    const Item = require('prismarine-item')('bedrock_1.17.10')

    it('stone sword (unenchanted)', () => {
      const item = Item.fromNotch({ network_id: 704, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: false, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([])
    })
    it('unbreaking 1 iron pickaxe', () => {
      const item = Item.fromNotch({ network_id: 716, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 17 }, lvl: { type: 'short', value: 1 } }] } } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 1, name: 'unbreaking' }])
    })
    it('efficiency 5 diamond shovel', () => {
      const item = Item.fromNotch({ network_id: 720, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 15 }, lvl: { type: 'short', value: 5 } }] } } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 5, name: 'efficiency' }])
    })
    it('protection 4, mending diamond leggings', () => {
      const item = Item.fromNotch({ network_id: 752, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 0 }, lvl: { type: 'short', value: 4 } }, { id: { type: 'short', value: 26 }, lvl: { type: 'short', value: 1 } }] } } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 4, name: 'protection' }, { lvl: 1, name: 'mending' }])
    })
  })
  describe('bedrock_1.19.1 test', () => {
    const Item = require('prismarine-item')('bedrock_1.19.1')

    it('iron hoe (unenchanted)', () => {
      const item = Item.fromNotch({ network_id: 754, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: false, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([])
    })
    it('silk touch stone axe', () => {
      const item = Item.fromNotch({ network_id: 743, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 16 }, lvl: { type: 'short', value: 1 } }] } } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 1, name: 'silk_touch' }])
    })
    it('lure 3 fishing rod', () => {
      const item = Item.fromNotch({ network_id: 836, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 24 }, lvl: { type: 'short', value: 3 } }] } } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 3, name: 'lure' }])
    })
    it('fire prot 3, unbreaking 2, respiration 3 diamond helmet', () => {
      const item = Item.fromNotch({ network_id: 786, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 1 }, lvl: { type: 'short', value: 3 } }, { id: { type: 'short', value: 17 }, lvl: { type: 'short', value: 2 } }, { id: { type: 'short', value: 6 }, lvl: { type: 'short', value: 3 } }] } } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      expect(enchs).toStrictEqual([{ lvl: 3, name: 'fire_protection' }, { lvl: 2, name: 'unbreaking' }, { lvl: 3, name: 'respiration' }])
    })
  })
})
describe('item.spawnEggMobName', () => {
  describe('1.8.9 test', () => {
    it('zombie egg', () => {
      const Item = require('prismarine-item')('1.8.9')
      const item = Item.fromNotch({ blockId: 383, itemCount: 1, itemDamage: 54 })
      expect(item.spawnEggMobName).toStrictEqual('Zombie')
    })
  })
  describe('1.11.2 test', () => {
    it('zombie egg', () => {
      const Item = require('prismarine-item')('1.11.2')
      const item = Item.fromNotch({ blockId: 383, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { EntityTag: { type: 'compound', value: { id: { type: 'string', value: 'minecraft:zombie' } } } } } })
      expect(item.spawnEggMobName).toStrictEqual('zombie')
    })
  })
  describe('1.11.2 test', () => {
    it('zombie egg', () => {
      const Item = require('prismarine-item')('1.11.2')
      const item = Item.fromNotch({ blockId: 383, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { EntityTag: { type: 'compound', value: { id: { type: 'string', value: 'minecraft:zombie' } } } } } })
      expect(item.spawnEggMobName).toStrictEqual('zombie')
    })
  })
  describe('1.11.2 test', () => {
    it('zombie egg', () => {
      const Item = require('prismarine-item')('1.11.2')
      const item = Item.fromNotch({ blockId: 383, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { EntityTag: { type: 'compound', value: { id: { type: 'string', value: 'minecraft:zombie' } } } } } })
      expect(item.spawnEggMobName).toStrictEqual('zombie')
    })
  })
  describe('1.16.5 test', () => {
    it('zombie egg', () => {
      const Item = require('prismarine-item')('1.16.5')
      const item = Item.fromNotch({ present: true, itemId: 819, itemCount: 1 })
      expect(item.spawnEggMobName).toStrictEqual('zombie')
    })
  })
  describe('bedrock_1.17.10 test', () => {
    it('zombie egg', () => {
      const Item = require('prismarine-item')('bedrock_1.17.10')
      const item = Item.fromNotch({ network_id: 936, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: false, can_place_on: [], can_destroy: [] } })
      expect(item.spawnEggMobName).toStrictEqual('zombie')
    })
  })
  describe('bedrock_1.19.1 test', () => {
    it('zombie egg', () => {
      const Item = require('prismarine-item')('bedrock_1.19.1')
      const item = Item.fromNotch({ network_id: 979, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: false, can_place_on: [], can_destroy: [] } })
      expect(item.spawnEggMobName).toStrictEqual('zombie')
    })
  })
})
describe('set item.enchants', () => {
  describe('1.8.8 test', () => {
    const Item = require('prismarine-item')('1.8.8')

    it('diamond axe with fortune 2', () => {
      const newItem = new Item(279, 1)
      const item = Item.fromNotch({ blockId: 279, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 2 }, id: { type: 'short', value: 35 } }] } }, RepairCost: { type: 'int', value: 1 } } } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 1
      expect(newItem).toStrictEqual(item)
    })

    it('gold helmet with fire prot 3, aqua afin 1, unbr 2', () => {
      const newItem = new Item(314, 1)
      const item = Item.fromNotch({ blockId: 314, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 3 }, id: { type: 'short', value: 1 } }, { lvl: { type: 'short', value: 2 }, id: { type: 'short', value: 34 } }, { lvl: { type: 'short', value: 1 }, id: { type: 'short', value: 6 } }] } }, RepairCost: { type: 'int', value: 3 } } } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 3
      expect(newItem).toStrictEqual(item)
    })

    it('carrot on stick with unbr 1', () => {
      const newItem = new Item(398, 1)
      const item = Item.fromNotch({ blockId: 398, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 1 }, id: { type: 'short', value: 34 } }] } }, RepairCost: { type: 'int', value: 1 } } } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 1
      expect(newItem).toStrictEqual(item)
    })

    it('stone pick with eff 4', () => {
      const newItem = new Item(274, 1)
      const item = Item.fromNotch({ blockId: 274, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 4 }, id: { type: 'short', value: 32 } }] } }, RepairCost: { type: 'int', value: 1 } } } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 1
      expect(newItem).toStrictEqual(item)
    })

    it('fishing rod with luck 3 lure 3', () => {
      const newItem = new Item(346, 1)
      const item = Item.fromNotch({ blockId: 346, itemCount: 1, itemDamage: 0, nbtData: { type: 'compound', name: '', value: { ench: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 3 }, id: { type: 'short', value: 61 } }, { lvl: { type: 'short', value: 3 }, id: { type: 'short', value: 62 } }] } }, RepairCost: { type: 'int', value: 3 } } } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 3
      expect(newItem).toStrictEqual(item)
    })
  })
  describe('1.16.5 test', () => {
    const Item = require('prismarine-item')('1.16.5')
    it('diamond sword (unenchanted)', () => {
      const newItem = new Item(603, 1)
      const item = Item.fromNotch({ present: true, itemId: 603, itemCount: 1, nbtData: { type: 'compound', name: '', value: { Damage: { type: 'int', value: 0 } } } })
      const enchs = item.enchants
      newItem.enchants = enchs
      expect(newItem).toStrictEqual(item)
    })
    it('iron shovel w/ eff2 for2 ub2', () => {
      const newItem = new Item(600, 1)
      const item = Item.fromNotch({ present: true, itemId: 600, itemCount: 1, nbtData: { type: 'compound', name: '', value: { RepairCost: { type: 'int', value: 3 }, Damage: { type: 'int', value: 0 }, Enchantments: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 2 }, id: { type: 'string', value: 'minecraft:efficiency' } }, { lvl: { type: 'short', value: 2 }, id: { type: 'string', value: 'minecraft:fortune' } }, { lvl: { type: 'short', value: 2 }, id: { type: 'string', value: 'minecraft:unbreaking' } }] } } } } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 3
      expect(newItem).toStrictEqual(item)
    })
    it('ench book w/ resp1 blastprot 1', () => {
      const newItem = new Item(848, 1)
      const item = Item.fromNotch({ present: true, itemId: 848, itemCount: 1, nbtData: { type: 'compound', name: '', value: { StoredEnchantments: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 1 }, id: { type: 'string', value: 'minecraft:respiration' } }, { lvl: { type: 'short', value: 1 }, id: { type: 'string', value: 'minecraft:blast_protection' } }] } }, RepairCost: { type: 'int', value: 1 } } } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 1
      expect(newItem).toStrictEqual(item)
    })
    it('fishing rod w/ mending', () => {
      const newItem = new Item(684, 1)
      const item = Item.fromNotch({ present: true, itemId: 684, itemCount: 1, nbtData: { type: 'compound', name: '', value: { RepairCost: { type: 'int', value: 1 }, Damage: { type: 'int', value: 0 }, Enchantments: { type: 'list', value: { type: 'compound', value: [{ lvl: { type: 'short', value: 1 }, id: { type: 'string', value: 'minecraft:mending' } }] } } } } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 1
      expect(newItem).toStrictEqual(item)
    })
  })
  describe('bedrock_1.17.10 test', () => {
    const registry = require('prismarine-registry')('bedrock_1.17.10')
    const Item = require('prismarine-item')(registry)

    it('unenchanted stone sword', () => {
      const newItem = new Item(704, 1, undefined, undefined, 0, true)
      const item = Item.fromNotch({ network_id: 704, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: false, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      newItem.enchants = enchs
      expect(newItem).toStrictEqual(item)
    })
    it('unbreaking 1 iron pickaxe', () => {
      const newItem = new Item(716, 1, undefined, undefined, 1, true)
      const item = Item.fromNotch({ network_id: 716, count: 1, metadata: 0, stack_id: 1, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 17 }, lvl: { type: 'short', value: 1 } }] } }, RepairCost: { type: 'int', value: 3 } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 3
      expect(newItem).toStrictEqual(item)
    })
    it('efficiency 5 diamond shovel', () => {
      const newItem = new Item(720, 1, undefined, undefined, 2, true)
      const item = Item.fromNotch({ network_id: 720, count: 1, metadata: 0, stack_id: 2, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 15 }, lvl: { type: 'short', value: 5 } }] } }, RepairCost: { type: 'int', value: 2 } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 2
      expect(newItem).toStrictEqual(item)
    })
    it('protection 4, mending diamond leggings', () => {
      const newItem = new Item(752, 1, undefined, undefined, 3, true)
      const item = Item.fromNotch({ network_id: 752, count: 1, metadata: 0, stack_id: 3, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 0 }, lvl: { type: 'short', value: 4 } }, { id: { type: 'short', value: 26 }, lvl: { type: 'short', value: 1 } }] } }, RepairCost: { type: 'int', value: 3 } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 3
      expect(newItem).toStrictEqual(item)
    })
  })
  describe('bedrock_1.19.1 test', () => {
    const Item = require('prismarine-item')('bedrock_1.19.1')

    it('unenchanted iron hoe', () => {
      const newItem = new Item(754, 1, undefined, undefined, 0, true)
      const item = Item.fromNotch({ network_id: 754, count: 1, metadata: 0, stack_id: 0, has_stack_id: true, extra: { has_nbt: false, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      newItem.enchants = enchs
      expect(newItem).toStrictEqual(item)
    })
    it('silk touch stone axe', () => {
      const newItem = new Item(743, 1, undefined, undefined, 1, true)
      const item = Item.fromNotch({ network_id: 743, count: 1, metadata: 0, stack_id: 1, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 16 }, lvl: { type: 'short', value: 1 } }] } }, RepairCost: { type: 'int', value: 1 } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 1
      expect(newItem).toStrictEqual(item)
    })
    it('lure 3 fishing rod', () => {
      const newItem = new Item(836, 1, undefined, undefined, 2, true)
      const item = Item.fromNotch({ network_id: 836, count: 1, metadata: 0, stack_id: 2, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 24 }, lvl: { type: 'short', value: 3 } }] } }, RepairCost: { type: 'int', value: 2 } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 2
      expect(newItem).toStrictEqual(item)
    })
    it('fire prot 3, unbreaking 2, respiration 3 diamond helmet', () => {
      const newItem = new Item(786, 1, undefined, undefined, 3, true)
      const item = Item.fromNotch({ network_id: 786, count: 1, metadata: 0, stack_id: 3, has_stack_id: true, extra: { has_nbt: true, nbt: { version: 1, nbt: { name: '', type: 'compound', value: { ench: { type: 'list', value: { type: 'compound', value: [{ id: { type: 'short', value: 1 }, lvl: { type: 'short', value: 3 } }, { id: { type: 'short', value: 17 }, lvl: { type: 'short', value: 2 } }, { id: { type: 'short', value: 6 }, lvl: { type: 'short', value: 3 } }] } }, RepairCost: { type: 'int', value: 3 } } } }, can_place_on: [], can_destroy: [] } })
      const enchs = item.enchants
      newItem.enchants = enchs
      newItem.repairCost = 3
      expect(newItem).toStrictEqual(item)
    })
  })
})

describe('use Item.equal', () => {
  const Item = require('prismarine-item')('1.16.5')
  const registry = require('prismarine-registry')('1.16.5')
  it('sh5 wep + not sh5 wep', () => {
    const itemOne = new Item(registry.itemsByName.diamond_sword.id, 1)
    itemOne.enchants = [{ name: 'sharpness', lvl: 5 }]
    const itemTwo = new Item(registry.itemsByName.diamond_sword.id, 1)
    expect(Item.equal(itemOne, itemTwo)).toStrictEqual(false)
  })
  it('two unenchanted', () => {
    const itemOne = new Item(registry.itemsByName.diamond_sword.id, 1)
    const itemTwo = new Item(registry.itemsByName.diamond_sword.id, 1)
    expect(Item.equal(itemOne, itemTwo)).toStrictEqual(true)
  })
  it('two enchanted', () => {
    const itemOne = new Item(registry.itemsByName.diamond_sword.id, 1)
    itemOne.enchants = [{ name: 'sharpness', lvl: 5 }]
    const itemTwo = new Item(registry.itemsByName.diamond_sword.id, 1)
    itemTwo.enchants = [{ name: 'sharpness', lvl: 5 }]
    expect(Item.equal(itemOne, itemTwo)).toStrictEqual(true)
  })
  it('two enchants in common on both items but diff orders', () => {
    const itemOne = new Item(registry.itemsByName.diamond_sword.id, 1)
    itemOne.enchants = [{ name: 'sharpness', lvl: 5 }, { name: 'unbreaking', lvl: 1 }]
    const itemTwo = new Item(registry.itemsByName.diamond_sword.id, 1)
    itemTwo.enchants = [{ name: 'unbreaking', lvl: 1 }, { name: 'sharpness', lvl: 5 }]
    expect(Item.equal(itemOne, itemTwo)).toStrictEqual(false)
  })
})

describe('durabilityUsed with damage component', () => {
  const Item = require('prismarine-item')('1.20.5')

  it('should return correct durabilityUsed for item with damage component', () => {
    const item = Item.fromNotch({
      itemId: 830,
      itemCount: 1,
      components: [
        {
          type: 'damage',
          data: 15
        }
      ]
    })
    expect(item.durabilityUsed).toBe(15)
  })
})
