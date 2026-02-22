/// <reference types="node" />
/// <reference types="prismarine-item" />

import {EventEmitter} from 'events';
import TypedEmitter from 'typed-emitter'
import {Item} from 'prismarine-item';

export class Window<T = unknown> extends (EventEmitter as new <T>() => TypedEmitter<T>)<T> {
    constructor (id: number, type: number | string, title: string, slotCount: number, inventorySlotsRange: { start: number, end: number }, craftingResultSlot: number, requiresConfirmation: boolean);

    /**
     * The protocol id of the window
     */
    id: number;

    /**
     * Type of the window, can be a string or a numeric id depending on the mcVersion
     */
    type: number | string;

    /**
     * Title of the window, shown in the gui
     */
    title: string;

    /**
     * Map of slot index to Item instance. null if the slot is empty
     */
    slots: Array<Item | null>;

    /**
     * Slot from where the player inventory start in the window
     */
    inventoryStart: number;

    /**
     * Slot from where the player inventory end in the window
     */
    inventoryEnd: number;

    /**
     * Slot from where the player hotbar start in the window.
     */
    hotbarStart: number;

    /**
     * Slot for the crafting result if this window has one, -1 otherwise.
     */
    craftingResultSlot: number;

    /**
     * Boolean only false for chests in pre-1.14 versions.
     */
    requiresConfirmation: boolean;

    /**
     * In vanilla client, this is the item you are holding with the mouse cursor.
     */
    selectedItem: Item | null;

    /**
     * accepts Clicks of with any mode, mouseButton and slot
     * @param click click object to accept
     * @param gamemode to know when certain clicks are allowed
     */
    acceptClick(click: Click, gamemode: number): void;

    /** @deprecated use {@link acceptClick} instead */
    acceptOutsideWindowClick(click: Click): void;

    /** @deprecated use {@link acceptClick} instead */
    acceptInventoryClick(click: Click): void;

    /** @deprecated use {@link acceptClick} instead */
    acceptNonInventorySwapAreaClick(click: Click): void;

    /** @deprecated use {@link acceptClick} instead */
    acceptSwapAreaLeftClick(click: Click): void;

    /** @deprecated use {@link acceptClick} instead */
    acceptSwapAreaRightClick(click: Click): void;

    /** @deprecated use {@link acceptClick} instead */
    acceptCraftingClick(click: Click): void;

    /**
     * See click types here https://wiki.vg/Protocol#Click_Window
     */

    /**
     * Accepts click mode 0 with mouseButton 0 or 1
     */
    mouseClick(click: Click): void;

    /**
     * Accepts click mode 1 with mouseButton 0 or 1 (identical behaviour)
     */
    shiftClick(click: Click): void;

    /**
     * Accepts click mode 2 with mouseButton 0 (hotbarStart) to 8 (hotbarEnd) representing the hotbar slots
     */
    numberClick(click: Click): void;

    /**
     * Accepts click mode 3 with mouseButton 2 (gets a stack of the item at the slot into the selectedItem)
     */
    middleClick(click: Click, gamemode: number): void;

    /**
     * Accepts click mode 4 with mouseButton 0 (drops one of the item) or 1 (drops all of the item)
     */
    dropClick(click: Click): void;

    /**
     * Fills within specified range with given item and dumps remaining items if present and possible
     * @param item item used to fill slots
     * @param start start slot to begin the search from
     * @param end end slot to end the search
     * @param lastToFirst if true the matching Slots will be filled from the back
     */
    fillAndDump(item: Item, start: number, end: number, lastToFirst: boolean): void;

    /**
     * Fills slots with specified item
     * @param slots slots to fill with the item
     * @param lastToFirst if true the matching Slots will be filled from the back
     */
    fillSlotsWithItem(slots: Array<Item>, item: Item, lastToFirst: boolean): void;

    /**
     * Fills slot with specified item
     * @param itemToFill item of which the count should be increased
     * @param itemToTake item of which the count should be decreased
     */
    fillSlotWithItem(itemToFill: Item, itemToTake: Item): void;

    /**
     * Fills slot with selectedItem (the item held in mouse cursor)
     * @param item item of which the count should be increased
     * @param untilFull if true as many as possible will be transfered
     */
    fillSlotWithSelectedItem (item: Item, untilFull: boolean): void;

    /**
     * Searches for empty slot to dump the specified item
     * @param item item which should be dumped
     * @param start start slot to begin the search from
     * @param end end slot to end the search
     * @param lastToFirst if true item slot will be searched from the back
     */
    dumpItem(item: Item, start: number, end: number, lastToFirst: boolean): void;

    /**
     * Splits the slot in half and holds the split in mouse cursor
     * @param item item to split
     */
    splitSlot(item: Item): void;

    /**
     * Swaps item with the item in mouse cursor
     * @param item item to swap with
     */
    swapSelectedItem(item: Item): void;

    /**
     * Drops item held in mouse cursor
     * @param untilEmpty if true whole item stack will be dropped (else just one)
     */
    dropSelectedItem(untilEmpty: boolean): void;

    /**
     * Change the slot to contain the newItem. Emit the updateSlot events.
     * @param slot {number}
     * @param newItem {Item}
     */
    updateSlot(slot: number, newItem: Item): void;

    /**
     * Returns array of items in the given range matching the one specified
     * @param start start slot to begin the search from
     * @param end end slot to end the search
     * @param itemType numerical id that you are looking for
     * @param metadata metadata value that you are looking for. null means unspecified
     * @param notFull (optional) - if true, means that the returned item should not be at its stackSize
     * @param nbt nbt data for the item you are looking for. null means unspecified
     */
    findItemsRange(start: number, end: number, itemType: number, metadata: number | null, notFull: boolean, nbt: any): Array<Item> | null;

    /**
     * Returns item in the given range matching the one specified
     * @param start start slot to begin the search from
     * @param end end slot to end the search
     * @param itemType numerical id that you are looking for
     * @param metadata metadata value that you are looking for. null means unspecified
     * @param notFull (optional) - if true, means that the returned item should not be at its stackSize
     * @param nbt nbt data for the item you are looking for. null means unspecified
     */
    findItemRange(start: number, end: number, itemType: number, metadata: number | null, notFull: boolean, nbt: any): Item | null;

    /**
     * @param start start slot to begin the search from
     * @param end end slot to end the search
     * @param itemName name that you are looking for
     * @param metadata metadata value that you are looking for. null means unspecified
     * @param notFull (optional) - if true, means that the returned item should not be at its stackSize
     */
    findItemRangeName(start: number, end: number, itemName: string, metadata: number | null, notFull: boolean): Item | null;

    /**
     * Search in the player inventory
     * @param itemType numerical id or name that you are looking for
     * @param metadata metadata value that you are looking for. null means unspecified
     * @param notFull (optional) - if true, means that the returned item should not be at its stackSize
     */
    findInventoryItem(itemType: number, metadata: number | null, notFull: boolean): Item | null;

    /**
     * Search in the container of the window
     * @param itemType numerical id or name that you are looking for
     * @param metadata metadata value that you are looking for. null means unspecified
     * @param notFull (optional) - if true, means that the returned item should not be at its stackSize
     */
    findContainerItem(itemType: number, metadata: number | null, notFull: boolean): Item | null;

    /**
     * Return the id of the first empty slot between start and end
     * @param start
     * @param end
     */
    firstEmptySlotRange(start: number, end: number): number | null;

    /**
     * Return the id of the first empty slot in the hotbar
     */
    firstEmptyHotbarSlot(): number | null

    /**
     * Return the id of the first empty slot in the container
     */
    firstEmptyContainerSlot() : number | null;

    /**
     * Return the id of the first empty slot in the inventory, start looking in the hotbar first if the flag is set
     * @param hotbarFirst DEFAULT: true
     */
    firstEmptyInventorySlot(hotbarFirst?: boolean): number | null;

    /**
     * Returns how much items there are ignoring what the item is, between slots start and end
     * @param start
     * @param end
     */
    sumRange(start: number, end: number): number;

    /**
     * Returns how many item you have of the given type, between slots start and end
     * @param start
     * @param end
     * @param itemType numerical id that you are looking for
     * @param metadata (optional) metadata value that you are looking for. defaults to unspecified
     */
    countRange(start: number, end: null, itemType: number, metadata: number | null): number;

    /**
     * Returns a list of Item instances between slots start and end
     * @param start
     * @param end
     */
    itemsRange(start: number, end: number): Array<Item>;

    /**
     * Returns how many you have in the inventory section of the window
     * @param itemType numerical id that you are looking for
     * @param metadata (optional) metadata value that you are looking for. defaults to unspecified
     */
    count(itemType: number | string, metadata: number | null): number;

    /**
     * Returns a list of Item instances from the inventory section of the window
     */
    items(): Array<Item>;

    /**
     * Returns how many you have in the top section of the window
     * @param itemType numerical id that you are looking for
     * @param metadata (optional) metadata value that you are looking for. defaults to unspecified
     */
    containerCount(itemType: number, metadata: number | null): number;

    /**
     * Returns a list of Item instances from the top section of the window
     */
    containerItems(): Array<Item>

    /**
     * Returns how many empty slots you have in the inventory section of the window
     */
    emptySlotCount(): number;

    /**
     * Returns the property: requiresConfirmation
     * @param click
     */
    transactionRequiresConfirmation(click?: Click): boolean;

    /**
     * Sets all slots in the window to null (unless specified by args)
     * @param blockId (optional) numerical id of the block that you would like to clear
     * @param count (optional, requires blockId) only delete this number of the given block
     */
    clear(blockId?: number, count?: number): void;
}
export interface Click {
    mode: number;
    mouseButton: number;
    slot: number;
}
export interface WindowInfo {
    type: number | string;
    inventory: { start: number, end: number };
    slots: number;
    craft: number;
    requireConfirmation: boolean;
}

export interface WindowsExports {
    createWindow(id: number, type: number | string, title: string, slotCount?: number): Window;
    Window: typeof Window;
    windows: {[key: string]: WindowInfo};
}
export declare function loader(mcVersion: string): WindowsExports;

export default loader;

export type WindowName =
    'minecraft:inventory' |
    'minecraft:generic_9x1' |
    'minecraft:generic_9x2' |
    'minecraft:generic_9x3' |
    'minecraft:generic_9x4' |
    'minecraft:generic_9x5' |
    'minecraft:generic_9x6' |
    'minecraft:generic_3x3' |
    'minecraft:anvil' |
    'minecraft:beacon' |
    'minecraft:blast_furnace' |
    'minecraft:brewing_stand' |
    'minecraft:crafting' |
    'minecraft:enchantment' |
    'minecraft:furnace' |
    'minecraft:grindstone' |
    'minecraft:hopper' |
    'minecraft:lectern' |
    'minecraft:loom' |
    'minecraft:merchant' |
    'minecraft:shulker_box' |
    'minecraft:smithing' |
    'minecraft:smoker' |
    'minecraft:cartography' |
    'minecraft:stonecutter'
