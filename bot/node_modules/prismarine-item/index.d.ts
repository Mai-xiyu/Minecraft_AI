/// <reference types="node" />

import { Tags, TagType } from 'prismarine-nbt'

export type ItemLike = Item | null

export class Item {
  constructor(type: number, count: number, metadata?: number, nbt?: object, stackId?: number, sentByServer?: boolean);
  type: number;
  slot: number;
  count: number;
  metadata: number;
  nbt: Tags[TagType] | null;
  stackId: number | null;
  name: string;
  displayName: string;
  stackSize: number;
  maxDurability: number;
  durabilityUsed: number;
  get enchants(): { name: string; lvl: number }[];
  set enchants(enchantments: { name: string; lvl: number }[]);
  get blocksCanPlaceOn(): [string][];
  set blocksCanPlaceOn(blockNames: string[]);
  get blocksCanDestroy(): [string][];
  set blocksCanDestroy(blockNames: string[]);
  repairCost: number;
  customName: string | null;
  customLore: string | string[] | null;
  readonly spawnEggMobName: string;
  static equal(item1: Item, item2: Item, matchStackSize?: boolean, matchNbt?: boolean): boolean;
  static toNotch(item: ItemLike, serverAuthoritative?: boolean): object;
  static fromNotch(item: object, stackId?: number): ItemLike;
  static anvil(
    itemOne: ItemLike,
    itemTwo: ItemLike,
    creative: boolean,
    rename: string | undefined
  ): { xpCost: number; item: ItemLike };
  static currentStackId: number;
  static nextStackId(): number;
}

export default function loader(mcVersion: string | object): typeof Item;
