const debug = require('debug')('prismarine-auth')

const { Endpoints } = require('../common/Constants')

class PlayfabTokenManager {
  constructor (cache) {
    this.cache = cache
  }

  async setCachedAccessToken (data) {
    await this.cache.setCachedPartial(data)
  }

  async getCachedAccessToken () {
    const { pfb: cache } = await this.cache.getCached()

    debug('[pf] token cache', cache)

    if (!cache) return

    const expires = new Date(cache.EntityToken.TokenExpiration)

    const remaining = expires - Date.now()

    const valid = remaining > 1000

    return { valid, until: expires, data: cache }
  }

  async getAccessToken (xsts) {
    const response = await fetch(Endpoints.PlayfabLoginWithXbox, {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        CreateAccount: true,
        EncryptedRequest: null,
        InfoRequestParameters: {
          GetCharacterInventories: false,
          GetCharacterList: false,
          GetPlayerProfile: true,
          GetPlayerStatistics: false,
          GetTitleData: false,
          GetUserAccountInfo: true,
          GetUserData: false,
          GetUserInventory: false,
          GetUserReadOnlyData: false,
          GetUserVirtualCurrency: false,
          PlayerStatisticNames: null,
          ProfileConstraints: null,
          TitleDataKeys: null,
          UserDataKeys: null,
          UserReadOnlyDataKeys: null
        },
        PlayerSecret: null,
        TitleId: '20CA2',
        XboxToken: `XBL3.0 x=${xsts.userHash};${xsts.XSTSToken}`
      })
    })

    const data = await response.json()

    await this.setCachedAccessToken({ pfb: data.data })

    return data.data
  }
}

module.exports = PlayfabTokenManager
