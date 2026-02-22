/// <reference types="node" />
import { Authflow } from "prismarine-auth";

declare module 'prismarine-realms' {
  export class RealmAPI {
    /**
     * Creates a new RealmAPI instance, which handles and authenticates calls to the Realms API
     * @param authflow An Authflow instance from [prismarine-auth](https://github.com/PrismarineJS/prismarine-auth).
     * @param platform Which platforms API to access
     */
    constructor(authflow: Authflow, platform: 'bedrock' | 'java')

    static from(authflow: Authflow, platform: 'bedrock' | 'java'): BedrockRealmAPI | JavaRealmAPI 

    getRealms(): Promise<Realm[]>
    getRealm(realmId: string): Promise<Realm>
    getRealmAddress(realmId: string): Promise<Address>
    getRealmBackups(realmId: string, slotId: string): Promise<Backup[]>
    getRealmWorldDownload(realmId: string, slotId: string, backupId?: string | 'latest'): Promise<Download>
    restoreRealmFromBackup(realmId: string, slotId: string, backupId: string): Promise<void>
    changeRealmState(realmId: string, state: 'open' | 'close'): Promise<void>

  }

  export class BedrockRealmAPI extends RealmAPI {
    getRealmFromInvite(realmInviteCode: string, invite: boolean): Promise<Realm>
    invitePlayer(realmId: string, uuid: string): Promise<Realm>
    getRealmInvite(realmId: string): Promise<RealmInvite>
    refreshRealmInvite(realmId: string): Promise<RealmInvite>
    getPendingInviteCount(): Promise<number>
    getPendingInvites(): Promise<RealmPlayerInvite[]>
    acceptRealmInvitation(invitationId: string): Promise<void>
    rejectRealmInvitation(invitationId: string): Promise<void>
    acceptRealmInviteFromCode(realmInviteCode: string): Promise<void>
  }

  export class JavaRealmAPI extends RealmAPI {
    invitePlayer(realmId: string, uuid: string, name: string): Promise<Realm>
  }

  export interface Realm {
    getAddress(): Promise<Address>
    invitePlayer(uuid: string, name: string): Promise<Realm>
    open(): Promise<void>
    close(): Promise<void>
    getBackups(): Promise<Backup[]>
    getWorldDownload(): Promise<Download>
    id: number
    remoteSubscriptionId: string
    owner: string | null
    ownerUUID: string
    name: string
    motd: string
    defaultPermission: string
    state: string
    daysLeft: number
    expired: boolean
    expiredTrial: boolean
    gracePeriod: boolean
    worldType: string
    players: RealmPlayer[] | null
    maxPlayers: number
    minigameName: string
    minigameId: number
    minigameImage: string
    activeSlot: number
    slots: Slot[] | null
    member: boolean
    clubId: number
    subscriptionRefreshStatus: null
  }

  export interface Backup {
    getDownload(): Promise<Download>
    restore(): Promise<void>
    id: string
    lastModifiedDate: number
    size: number
    metadata: {
        gameDifficulty: string
        name: string
        gameServerVersion: string
        enabledPacks: { 
          resourcePack: string
          behaviorPack: string
        }
        description: string | null
        gamemode: string
        worldType: string
    }
  }

  export interface Download {
    writeToDirectory(directory: string): Promise<void>
    getBuffer(): Promise<Buffer>
    downloadUrl: string
    fileExtension: '.mcworld' | '.tar.gz'
    resourcePackUrl?: string // Java only
    resourcePackHash?: string // Java only
    size?: number // Bedrock only
    token?: string // Bedrock only
  }

  export interface RealmPlayerInvite {
    invitationId: string
    worldName: string
    worldDescription: string
    worldOwnerName: string
    worldOwnerXUID: string
    createdOn: number
  }

  export interface RealmInvite {
    inviteCode: string,
    ownerXUID: string,
    type: string,
    createdOn: number,
    inviteLink: string,
    deepLinkUrl: string,
  }

  export interface RealmPlayer {
      uuid: string,
      name: string,
      operator: boolean,
      accepted: boolean,
      online: boolean,
      permission: string
  }

  export interface Slot {
      options: string
      slotId: number
  }

  export interface Address {
    host: string
    port: number
  }

}
