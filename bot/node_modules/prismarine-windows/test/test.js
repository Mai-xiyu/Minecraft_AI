/* eslint-env mocha */

const { describe, it, afterEach } = require('mocha')
const assert = require('assert')

const mcVersion = '1.8'
const registry = require('prismarine-registry')(mcVersion)
const windows = require('..')(registry)
const Item = require('prismarine-item')(registry)

function getAssertFunctions (slot) {
  return {
    isEmpty: function () {
      assert.equal(slot, null, 'slot is not empty')
      return this
    },
    isNotEmpty: function () {
      assert.notEqual(slot, null, 'slot is empty')
      return this
    },
    hasCount: function (count) {
      this.isNotEmpty()
      assert.equal(slot.count, count, 'slot count doesn\'t match')
      return this
    },
    hasMaxCount: function () {
      this.isNotEmpty()
      assert.equal(slot.count, slot.stackSize, 'slot doesn\'t have max count')
      return this
    },
    hasType: function (type) {
      this.isNotEmpty()
      assert.equal(slot.type, type, `slot doesn't have type ${type}`)
      return this
    }
  }
}

function getActualSlot (slotShorthand, inventoryEnd) {
  // negative values start from the end of the inventory
  return slotShorthand < 0 ? inventoryEnd + slotShorthand : slotShorthand
}

function getSlotShorthand (actualSlot, inventoryEnd) {
  const negativeSlotShorthand = actualSlot - inventoryEnd
  return Math.abs(negativeSlotShorthand) < actualSlot ? negativeSlotShorthand : actualSlot
}

function createTestWindow (type, slotCount = undefined) {
  const testWindow = windows.createWindow(1, 'minecraft:' + type, type, slotCount ?? (type === 'chest' ? 27 : undefined))

  testWindow.prepareSlot = function (slotShorthand, count, type) {
    testWindow.updateSlot(getActualSlot(slotShorthand, testWindow.inventoryEnd), new Item(type, count))

    return testWindow
  }

  testWindow.prepareSelectedItem = function (count, type) {
    testWindow.selectedItem = new Item(type, count)

    return testWindow
  }

  testWindow.executeClick = function (mode, mouseButton, slotShorthand, gamemode) {
    const slot = getActualSlot(slotShorthand, testWindow.inventoryEnd)
    const click = {
      slot,
      mouseButton,
      mode,
      windowId: testWindow.id,
      item: slot === -999 ? null : testWindow.slots[slot]
    }

    testWindow.updatedSlots = []
    testWindow.assertedSlots = []
    const onSlotUpdate = (slot) => {
      slot = +slot
      if (!testWindow.updatedSlots.includes(slot)) {
        testWindow.updatedSlots.push(slot)
      }
    }

    testWindow.on('updateSlot', onSlotUpdate)

    const changedSlots = testWindow.acceptClick(click, gamemode)

    testWindow.removeListener('updateSlot', onSlotUpdate)

    return changedSlots
  }

  testWindow.assertSlot = function (slotShorthand) {
    let slot = getActualSlot(slotShorthand, testWindow.inventoryEnd)
    if (!testWindow.assertedSlots.includes(slot)) {
      testWindow.assertedSlots.push(slot)
    }
    slot = testWindow.slots[slot]
    return getAssertFunctions(slot)
  }

  testWindow.assertSelectedItem = function () {
    return getAssertFunctions(testWindow.selectedItem)
  }

  return testWindow
}

// item ids
const firstItem = 1
const secondItem = 2

let testWindow = null

afterEach(function () {
  testWindow.updatedSlots.forEach((slot) => {
    if (!testWindow.assertedSlots.includes(slot)) {
      const slotShorthand = getSlotShorthand(slot, testWindow.inventoryEnd)
      assert.fail(`slot ${slotShorthand}${slotShorthand !== slot ? ` (actual: ${slot})` : ''} updated, but has not been asserted`)
    }
  })
})

describe('mode 0 | normal click', () => {
  describe('mouseButton 0', () => {
    it('pickup item', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(0, 64, firstItem)

      testWindow.executeClick(0, 0, 0)

      testWindow.assertSlot(0).isEmpty()
      testWindow.assertSelectedItem().hasCount(64).hasType(firstItem)
    })
  })

  describe('mouseButton 1', () => {
    it('drop one of selected Item into a slot (same item)', () => {
      testWindow = createTestWindow('chest')
        .prepareSelectedItem(64, firstItem)
        .prepareSlot(0, 1, firstItem)

      testWindow.executeClick(0, 1, 0)

      testWindow.assertSelectedItem().hasCount(63)
      testWindow.assertSlot(0).hasCount(2)
    })

    it('drop one of selected Item into a slot (empty slot)', () => {
      testWindow = createTestWindow('chest')
        .prepareSelectedItem(64, firstItem)

      testWindow.executeClick(0, 1, 0)

      testWindow.assertSelectedItem().hasCount(63)
      testWindow.assertSlot(0).hasCount(1)
    })

    it('drop selected Item into a slot (empty slot)', () => {
      testWindow = createTestWindow('chest')
        .prepareSelectedItem(1, firstItem)

      testWindow.executeClick(0, 1, 0)

      testWindow.assertSelectedItem().isEmpty()
      testWindow.assertSlot(0).hasCount(1)
    })
  })

  describe('mouseButton 0', () => {
    it('drop all of selected Item into a slot (almost full with same item)', () => {
      testWindow = createTestWindow('chest')
        .prepareSelectedItem(64, firstItem)
        .prepareSlot(0, 60, firstItem)

      testWindow.executeClick(0, 0, 0)

      testWindow.assertSelectedItem().hasCount(60)
      testWindow.assertSlot(0).hasCount(64)
    })

    it('drop selected Item into empty slot', () => {
      testWindow = createTestWindow('chest')
        .prepareSelectedItem(1, firstItem)

      testWindow.executeClick(0, 0, 0)

      testWindow.assertSelectedItem().isEmpty()
      testWindow.assertSlot(0).isNotEmpty().hasCount(1).hasType(firstItem)
    })
  })
})

describe('mode 1 | shift click', () => {
  describe('mouseButton 0', () => {
    it('shift out of chest into inventory', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(0, 64, firstItem)

      testWindow.executeClick(1, 0, 0)

      testWindow.assertSlot(0).isEmpty()
      testWindow.assertSlot(-1).isNotEmpty().hasCount(64).hasType(firstItem)
    })

    it('shift out of inventory into chest', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(-1, 64, firstItem)

      testWindow.executeClick(1, 0, -1)

      testWindow.assertSlot(0).isNotEmpty().hasCount(64).hasType(firstItem)
      testWindow.assertSlot(-1).isEmpty()
    })

    it.skip('shift out of inventory into armor slot (unimplemented)', () => {
      const someBoots = registry.itemsByName.leather_boots.id
      testWindow = createTestWindow('inventory')
        .prepareSlot(-1, 1, someBoots)

      testWindow.executeClick(1, 0, -1)

      testWindow.assertSlot(-1).isEmpty()
      // 8 is the slot for boots
      testWindow.assertSlot(8).isNotEmpty().hasType(someBoots).hasCount(1)
    })
  })
})

describe('mode 2 | number click', () => {
  describe('mouseButton 0', () => {
    it('from full slot into empty slot', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(0, 64, firstItem)

      // mouseButton 0 = hotbarStart
      // slot 0 = windowStart
      testWindow.executeClick(2, 0, 0)

      testWindow.assertSlot(-9).isNotEmpty().hasCount(64).hasType(firstItem)
      testWindow.assertSlot(0).isEmpty()
    })

    it('from empty slot into full slot', () => {
      testWindow = createTestWindow('chest')
        // -9 = hotbarStart
        .prepareSlot(-9, 64, firstItem)

      // mouseButton 0 = hotbarStart
      // slot 0 = windowStart
      testWindow.executeClick(2, 0, 0)

      testWindow.assertSlot(-9).isEmpty()
      testWindow.assertSlot(0).isNotEmpty().hasCount(64).hasType(firstItem)
    })

    it('from slot with item to slot with same item', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(-9, 32, firstItem)
        .prepareSlot(0, 32, firstItem)

      testWindow.executeClick(2, 0, 0)

      if (registry.version['>=']('1.9')) {
        // expect nothing to happen
        testWindow.assertSlot(0).hasCount(32)
        testWindow.assertSlot(-9).hasCount(32)
      } else {
        testWindow.assertSlot(0).isEmpty()
        testWindow.assertSlot(-9).isNotEmpty().hasCount(64).hasType(firstItem)
        testWindow.assertSlot(-8).isEmpty()
      }
    })

    it('from slot with item to slot with different item', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(0, 64, firstItem)
        .prepareSlot(-1, 64, secondItem)

      // mouseButton 8 = hotbarEnd
      // slot 0 = windowStart
      testWindow.executeClick(2, 8, 0)

      if (registry.version['>=']('1.9')) {
        testWindow.assertSlot(0).isNotEmpty().hasCount(64).hasType(secondItem)
        testWindow.assertSlot(-1).isNotEmpty().hasCount(64).hasType(firstItem)
      } else {
        testWindow.assertSlot(0).isEmpty()
        testWindow.assertSlot(-1).isNotEmpty().hasCount(64).hasType(firstItem)
        testWindow.assertSlot(-9).isNotEmpty().hasCount(64).hasType(secondItem)
      }
    })

    it('same slot click does nothing', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(62, 64, firstItem)

      // slot 62 = hotbarEnd
      // mouseButton 8 = hotbarEnd
      // slot 0 = windowStart
      testWindow.executeClick(2, 8, 62)

      // no asserts, test would fail regardless
      // if something did change
    })
  })
})

describe('mode 3 | middle click', () => {
  describe('mouseButton 2', () => {
    it('get stack into selectedItem (gamemode 0)', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(0, 1, firstItem)

      testWindow.executeClick(3, 2, 0)

      // expect no change
      testWindow.assertSelectedItem().isEmpty()
    })

    it('get stack into selectedItem (gamemode 1)', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(0, 1, firstItem)

      testWindow.executeClick(3, 2, 0, /* gamemode = */1)

      testWindow.assertSelectedItem().isNotEmpty().hasCount(64).hasType(firstItem)
    })
  })
})

describe('mode 4 | drop click', () => {
  describe('mouseButton 0', () => {
    it('drop 1 of stack', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(0, 64, firstItem)

      testWindow.executeClick(4, 0, 0)

      testWindow.assertSlot(0).isNotEmpty().hasCount(64 - 1).hasType(firstItem)
    })
  })

  describe('mouseButton 1', () => {
    it('drop full stack', () => {
      testWindow = createTestWindow('chest')
        .prepareSlot(0, 64, firstItem)

      testWindow.executeClick(4, 1, 0)

      testWindow.assertSlot(0).isEmpty()
    })
  })
})

it('returning changed slots works', () => {
  testWindow = createTestWindow('chest')
    .prepareSlot(0, 64, firstItem)

  const changedSlots = testWindow.executeClick(0, 0, 0)

  testWindow.assertSlot(0).isEmpty()
  testWindow.assertSelectedItem().isNotEmpty()

  assert.equal(changedSlots.length, 1)
  assert.equal(changedSlots[0], 0)
  // selectedItem isn't included in changedSlots
})
