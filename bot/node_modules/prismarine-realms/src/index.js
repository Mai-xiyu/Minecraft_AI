const Rest = require('./rest')

const Realm = require('./structures/Realm')
const Backup = require('./structures/Backup')

class RealmAPI {
  constructor (authflow, platform, options = {}) {
    this.rest = new Rest(authflow, platform, options)
    this.platform = platform
  }

  static from (authflow, platform, options) {
    return new {
      java: require('./java/api'),
      bedrock: require('./bedrock/api')
    }[platform](authflow, platform, options)
  }

  async getRealm (realmId) {
    const data = await this.rest.get(`/worlds/${realmId}`)
    return new Realm(this, data)
  }

  async getRealms () {
    const data = await this.rest.get('/worlds')
    return data.servers.map(realm => new Realm(this, realm))
  }

  async getRealmBackups (realmId, slotId) {
    const data = await this.rest.get(`/worlds/${realmId}/backups`)
    return data.backups.map(e => new Backup(this, { realmId, slotId }, e))
  }

  async restoreRealmFromBackup (realmId, backupId) {
    return await this.rest.put(`/worlds/${realmId}/backups?backupId=${encodeURIComponent(backupId)}&clientSupportsRetries`)
  }
}

module.exports = RealmAPI
