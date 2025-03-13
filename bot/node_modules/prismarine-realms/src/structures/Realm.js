module.exports = class Realm {
  #api
  constructor (api, data) {
    this.#api = api
    Object.assign(this, {
      id: data.id,
      remoteSubscriptionId: data.remoteSubscriptionId,
      owner: data.owner,
      ownerUUID: data.ownerUUID,
      name: data.name,
      motd: data.motd,
      defaultPermission: data.defaultPermission,
      state: data.state,
      daysLeft: data.daysLeft,
      expired: data.expired,
      expiredTrial: data.expiredTrial,
      gracePeriod: data.gracePeriod,
      worldType: data.worldType,
      players: data.players,
      maxPlayers: data.maxPlayers,
      minigameName: data.minigameName,
      minigameId: data.minigameId,
      minigameImage: data.minigameImage,
      activeSlot: data.activeSlot,
      slots: data.slots,
      member: data.member,
      clubId: data.clubId,
      subscriptionRefreshStatus: data.subscriptionRefreshStatus
    })
  }

  async getAddress () {
    return this.#api.getRealmAddress(this.id)
  }

  async invitePlayer (uuid, name) {
    return this.#api.invitePlayer(this.id, uuid, name)
  }

  async open () {
    return this.#api.changeRealmState(this.id, 'open')
  }

  async close () {
    return this.#api.changeRealmState(this.id, 'close')
  }

  async getWorldDownload () {
    return this.#api.getRealmWorldDownload(this.id, this.activeSlot, 'latest')
  }

  async getBackups () {
    return this.#api.getRealmBackups(this.id, this.activeSlot)
  }
}
