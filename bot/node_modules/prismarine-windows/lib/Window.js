const assert = require('assert')
const EventEmitter = require('events').EventEmitter

module.exports = (Item, registry) => {
  return class Window extends EventEmitter {
    constructor (id, type, title, slotCount,
      inventorySlotsRange = { start: 27, end: 62 },
      craftingResultSlot = -1,
      requiresConfirmation = true) {
      super()
      this.id = id
      this.type = type
      this.title = title
      this.slots = new Array(slotCount).fill(null)
      this.inventoryStart = inventorySlotsRange.start
      this.inventoryEnd = inventorySlotsRange.end + 1
      this.hotbarStart = this.inventoryEnd - 9
      this.craftingResultSlot = craftingResultSlot
      this.requiresConfirmation = requiresConfirmation
      // in vanilla client, this is the item you are holding with the
      // mouse cursor
      this.selectedItem = null
    }

    acceptClick (click, gamemode = 0) {
      const { mode, slot, mouseButton } = click
      assert.ok(
        (mode >= 0 && mode <= 6) &&
        (mouseButton >= 0 && mouseButton <= 8) &&
        ((slot >= 0 && slot < this.inventoryEnd) || slot === -999 ||
         (this.type === 'minecraft:inventory' && slot === 45)),
        'invalid operation')

      switch (click.mode) {
        case 0:
          assert.ok(mouseButton <= 1, 'invalid operation')
          return this.mouseClick(click)

        case 1:
          assert.ok(mouseButton <= 1, 'invalid operation')
          return this.shiftClick(click)

        case 2:
          assert.ok(mouseButton <= 8, 'invalid operation')
          return this.numberClick(click)

        case 3:
          assert.ok(mouseButton === 2, 'invalid operation')
          return this.middleClick(click, gamemode)

        case 4:
          assert.ok(mouseButton <= 1, 'invalid operation')
          return this.dropClick(click)

        case 5:
          assert.ok([1, 5, 9, 2, 6, 10].includes(mouseButton), 'invalid operation')
          return this.dragClick(click, gamemode)

        case 6:
          assert.ok(mouseButton === 0, 'invalid operation')
          return this.doubleClick(click)
      }
    }

    mouseClick (click) {
      if (click.slot === -999) {
        this.dropSelectedItem(click.mouseButton === 0)
      } else {
        let { item } = click
        if (click.mouseButton === 0) { // left click
          if (item && this.selectedItem) {
            if (Item.equal(item, this.selectedItem, false)) {
              if (click.slot === this.craftingResultSlot) {
                const maxTransferrable = this.selectedItem.stackSize - this.selectedItem.count
                if (item.count > maxTransferrable) {
                  this.selectedItem.count += maxTransferrable
                  item.count -= maxTransferrable
                } else if (item.count <= maxTransferrable) {
                  this.selectedItem.count += item.count
                  this.updateSlot(item.slot, null)
                }
              } else {
                this.fillSlotWithSelectedItem(item, true)
              }
            } else {
              this.swapSelectedItem(click.slot, item)
            }

            return [click.slot]
          } else if (this.selectedItem || item) {
            this.swapSelectedItem(click.slot, item)

            return [click.slot]
          }
        } else if (click.mouseButton === 1) { // right click
          if (this.selectedItem) {
            if (item) {
              if (Item.equal(item, this.selectedItem, false)) {
                this.fillSlotWithSelectedItem(item, false)
              } else {
                this.swapSelectedItem(click.slot, item)
              }
            } else {
              item = new Item(this.selectedItem.type, 0, this.selectedItem.metadata, this.selectedItem.nbt)
              this.updateSlot(click.slot, item)
              this.fillSlotWithSelectedItem(item, false)
            }

            return [click.slot]
          } else if (item && click.slot !== this.craftingResultSlot) {
            this.splitSlot(item)

            return [click.slot]
          }
        }
      }

      return []
    }

    shiftClick (click) {
      const { item } = click
      if (!item) return
      if (this.type === 'minecraft:inventory') {
        if (click.slot < this.inventoryStart) {
          this.fillAndDump(item, this.inventoryStart, this.inventoryEnd, click.slot === this.craftingResultSlot)
        } else {
          if (click.slot >= this.inventoryStart && click.slot < this.inventoryEnd - 10) {
            this.fillAndDump(item, this.hotbarStart, this.inventoryEnd)
          } else {
            this.fillAndDump(item, this.inventoryStart, this.inventoryEnd)
          }
        }
      } else {
        if (click.slot < this.inventoryStart) {
          this.fillAndDump(item, this.inventoryStart, this.inventoryEnd, this.craftingResultSlot === -1 || click.slot === this.craftingResultSlot)
        } else {
          this.fillAndDump(item, 0, this.inventoryStart - 1)
        }
      }
    }

    numberClick (click) {
      if (this.selectedItem) return
      const { item } = click
      const hotbarSlot = this.hotbarStart + click.mouseButton
      const itemAtHotbarSlot = this.slots[hotbarSlot]
      if (Item.equal(item, itemAtHotbarSlot) && item?.slot === hotbarSlot) return
      if (item) {
        if (itemAtHotbarSlot) {
          if ((this.type === 'minecraft:inventory' || registry.version['>=']('1.9')) && click.slot !== this.craftingResultSlot) {
            this.updateSlot(click.slot, itemAtHotbarSlot)
            this.updateSlot(hotbarSlot, item)
          } else {
            this.dumpItem(itemAtHotbarSlot, this.hotbarStart, this.inventoryEnd)
            if (this.slots[hotbarSlot]) {
              this.dumpItem(itemAtHotbarSlot, this.inventoryStart, this.hotbarStart - 1)
            }
            if (this.slots[hotbarSlot] === null) {
              this.updateSlot(item.slot, null)
              this.updateSlot(hotbarSlot, item)
              let slots = this.findItemsRange(this.hotbarStart, this.inventoryEnd, itemAtHotbarSlot.type, itemAtHotbarSlot.metadata, true, itemAtHotbarSlot.nbt)
              slots.push(...this.findItemsRange(this.inventoryStart, this.hotbarStart - 1, itemAtHotbarSlot.type, itemAtHotbarSlot.metadata, true, itemAtHotbarSlot.nbt))
              slots = slots.filter(slot => slot.slot !== itemAtHotbarSlot.slot)
              this.fillSlotsWithItem(slots, itemAtHotbarSlot)
            }
          }
        } else {
          this.updateSlot(item.slot, null)
          this.updateSlot(hotbarSlot, item)
        }
      } else if (itemAtHotbarSlot && click.slot !== this.craftingResultSlot) {
        this.updateSlot(click.slot, itemAtHotbarSlot)
        this.updateSlot(hotbarSlot, null)
      }
    }

    middleClick (click, gamemode) {
      if (this.selectedItem) return []
      const { item } = click
      if (gamemode === 1 && item) {
        this.selectedItem = new Item(item.type, item.stackSize, item.metadata, item.nbt)
      }
      return []
    }

    dropClick (click) {
      const { item } = click
      if (this.selectedItem || item === null) return []
      if (click.mouseButton === 0) {
        if (--click.item.count === 0) this.updateSlot(click.slot, null)
        return [click.slot]
      } else if (click.mouseButton === 1) {
        this.updateSlot(click.slot, null)
        return [click.slot]
      }
    }

    dragClick (click, gamemode) {
      // unimplemented
      assert.ok(false, 'unimplemented')
    }

    doubleClick (click) {
      // unimplemented
      assert.ok(false, 'unimplemented')
    }

    acceptOutsideWindowClick = this.acceptClick
    acceptInventoryClick = this.acceptClick
    acceptNonInventorySwapAreaClick = this.acceptClick
    acceptSwapAreaLeftClick = this.acceptClick
    acceptSwapAreaRightClick = this.acceptClick
    acceptCraftingClick = this.acceptClick

    fillAndDump (item, start, end, lastToFirst = false) {
      this.fillSlotsWithItem(this.findItemsRange(start, end, item.type, item.metadata, true, item.nbt, true), item, lastToFirst)
      if (this.slots[item.slot]) {
        this.dumpItem(item, start, end, lastToFirst)
      }
    }

    fillSlotsWithItem (slots, item, lastToFirst = false) {
      while (slots.length && item.count) {
        this.fillSlotWithItem(lastToFirst ? slots.pop() : slots.shift(), item)
      }
    }

    fillSlotWithItem (itemToFill, itemToTake) {
      const newCount = itemToFill.count + itemToTake.count
      const leftover = newCount - itemToFill.stackSize
      if (leftover <= 0) {
        itemToFill.count = newCount
        itemToTake.count = 0
        this.updateSlot(itemToTake.slot, null)
      } else {
        itemToFill.count = itemToFill.stackSize
        itemToTake.count = leftover
      }
    }

    fillSlotWithSelectedItem (item, untilFull) {
      if (untilFull) {
        const newCount = item.count + this.selectedItem.count
        const leftover = newCount - item.stackSize
        if (leftover <= 0) {
          item.count = newCount
          this.selectedItem = null
        } else {
          item.count = item.stackSize
          this.selectedItem.count = leftover
        }
      } else {
        if (item.count + 1 <= item.stackSize) {
          item.count++
          if (--this.selectedItem.count === 0) this.selectedItem = null
        }
      }
    }

    dumpItem (item, start, end, lastToFirst = false) {
      const emptySlot = lastToFirst ? this.lastEmptySlotRange(start, end) : this.firstEmptySlotRange(start, end)
      if (emptySlot !== null && emptySlot !== this.craftingResultSlot) {
        const slot = item.slot
        this.updateSlot(emptySlot, item)
        this.updateSlot(slot, null)
      }
    }

    splitSlot (item) {
      if (!item) return
      this.selectedItem = new Item(item.type, Math.ceil(item.count / 2), item.metadata, item.nbt)
      item.count -= this.selectedItem.count
      if (item.count === 0) this.updateSlot(item.slot, null)
    }

    swapSelectedItem (slot, item) {
      this.updateSlot(slot, this.selectedItem)
      this.selectedItem = item
    }

    dropSelectedItem (untilEmpty) {
      if (untilEmpty || --this.selectedItem.count === 0) this.selectedItem = null
    }

    updateSlot (slot, newItem) {
      if (newItem) newItem.slot = slot
      const oldItem = this.slots[slot]
      this.slots[slot] = newItem

      this.emit('updateSlot', slot, oldItem, newItem)
      this.emit(`updateSlot:${slot}`, oldItem, newItem)
    }

    findItemsRange (start, end, itemType, metadata, notFull, nbt, withoutCraftResultSlot = false) {
      const items = []
      while (start < end) {
        const item = this.findItemRange(start, end, itemType, metadata, notFull, nbt, withoutCraftResultSlot)
        if (!item) break
        start = item.slot + 1
        items.push(item)
      }
      return items
    }

    findItemRange (start, end, itemType, metadata, notFull, nbt, withoutCraftResultSlot = false) {
      assert.notStrictEqual(itemType, null)
      for (let i = start; i < end; ++i) {
        const item = this.slots[i]
        if (
          item && itemType === item.type &&
          (metadata == null || metadata === item.metadata) &&
          (!notFull || item.count < item.stackSize) &&
          (nbt == null || JSON.stringify(nbt) === JSON.stringify(item.nbt)) &&
          !(item.slot === this.craftingResultSlot && withoutCraftResultSlot)) {
          return item
        }
      }
      return null
    }

    findItemRangeName (start, end, itemName, metadata, notFull) {
      assert.notStrictEqual(itemName, null)
      for (let i = start; i < end; ++i) {
        const item = this.slots[i]
        if (item && itemName === item.name &&
          (metadata == null || metadata === item.metadata) &&
          (!notFull || item.count < item.stackSize)) {
          return item
        }
      }
      return null
    }

    findInventoryItem (item, metadata, notFull) {
      assert(typeof item === 'number' || typeof item === 'string' || typeof item === 'undefined', 'No valid type given')
      return typeof item === 'number'
        ? this.findItemRange(this.inventoryStart, this.inventoryEnd, item, metadata, notFull)
        : this.findItemRangeName(this.inventoryStart, this.inventoryEnd, item, metadata, notFull)
    }

    findContainerItem (item, metadata, notFull) {
      assert(typeof item === 'number' || typeof item === 'string' || typeof item === 'undefined', 'No valid type given')
      return typeof item === 'number'
        ? this.findItemRange(0, this.inventoryStart, item, metadata, notFull)
        : this.findItemRangeName(0, this.inventoryStart, item, metadata, notFull)
    }

    firstEmptySlotRange (start, end) {
      for (let i = start; i < end; ++i) {
        if (this.slots[i] === null) return i
      }
      return null
    }

    lastEmptySlotRange (start, end) {
      for (let i = end; i >= start; i--) {
        if (this.slots[i] === null) return i
      }
      return null
    }

    firstEmptyHotbarSlot () {
      return this.firstEmptySlotRange(this.hotbarStart, this.inventoryEnd)
    }

    firstEmptyContainerSlot () {
      return this.firstEmptySlotRange(0, this.inventoryStart)
    }

    firstEmptyInventorySlot (hotbarFirst = true) {
      if (hotbarFirst) {
        const slot = this.firstEmptyHotbarSlot()
        if (slot !== null) return slot
      }
      return this.firstEmptySlotRange(this.inventoryStart, this.inventoryEnd)
    }

    sumRange (start, end) {
      let sum = 0
      for (let i = start; i < end; i++) {
        const item = this.slots[i]
        if (item) sum += item.count
      }
      return sum
    }

    countRange (start, end, itemType, metadata) {
      let sum = 0
      for (let i = start; i < end; ++i) {
        const item = this.slots[i]
        if (item && itemType === item.type &&
          (metadata == null || item.metadata === metadata)) {
          sum += item.count
        }
      }
      return sum
    }

    itemsRange (start, end) {
      const results = []
      for (let i = start; i < end; ++i) {
        const item = this.slots[i]
        if (item) results.push(item)
      }
      return results
    }

    count (itemType, metadata) {
      itemType = parseInt(itemType, 10) // allow input to be string
      return this.countRange(this.inventoryStart, this.inventoryEnd, itemType, metadata)
    }

    items () {
      return this.itemsRange(this.inventoryStart, this.inventoryEnd)
    }

    containerCount (itemType, metadata) {
      itemType = parseInt(itemType, 10) // allow input to be string
      return this.countRange(0, this.inventoryStart, itemType, metadata)
    }

    containerItems () {
      return this.itemsRange(0, this.inventoryStart)
    }

    emptySlotCount () {
      let count = 0
      for (let i = this.inventoryStart; i < this.inventoryEnd; ++i) {
        if (this.slots[i] === null) count += 1
      }
      return count
    }

    transactionRequiresConfirmation (click) {
      return this.requiresConfirmation
    }

    clear (blockId, count) {
      let clearedCount = 0

      const iterLoop = (currSlot) => {
        if (!currSlot || (blockId && currSlot.type !== blockId)) return false
        const blocksNeeded = count - clearedCount
        if (count && currSlot.count > blocksNeeded) { // stack is bigger then needed
          clearedCount += blocksNeeded
          this.updateSlot(currSlot.slot, new Item(blockId, currSlot.count - blocksNeeded, currSlot.metadata, currSlot.nbt))
        } else { // stack is just big enough or too little items to finish counter
          clearedCount += currSlot.count
          this.updateSlot(currSlot.slot, null)
        }
        if (count === clearedCount) return true // we have enough items
        return false
      }

      for (let i = this.inventoryEnd; i > this.hotbarStart - 1; i--) {
        if (iterLoop(this.slots[i])) break
      }

      if (clearedCount !== count) {
        for (let i = this.inventoryStart; i < this.hotbarStart; i++) {
          if (iterLoop(this.slots[i])) break
        }
      }

      return clearedCount
    }
  }
}
