/* eslint-env mocha */
const nock = require('nock')

const { expect, use } = require('chai')
const chaiAsPromised = require('chai-as-promised')

use(chaiAsPromised)

const { World, Join, JavaWorldDownload, Backups } = require('./common/responses.json')

const { RealmAPI } = require('prismarine-realms')
const { Authflow } = require('prismarine-auth')

const Backup = require('../src/structures/Backup')
const Download = require('../src/structures/Download')

const config = {
  realmId: '1112223',
  slotId: '1',
  backupId: '1970-01-01T00:00:00.000Z',
  uuid: '1111222233334444',
  name: 'Steve'
}

const authflow = new Authflow()

const api = RealmAPI.from(authflow, 'java', { skipAuth: true })

nock('https://pc.realms.minecraft.net')
  .get('/worlds')
  .reply(200, { servers: [World] })
  .get(`/worlds/${config.realmId}`)
  .times(8)
  .reply(200, World)
  .get(`/worlds/v1/${config.realmId}/join/pc`)
  .reply(200, Join)
  .post(`/invites/${config.realmId}`)
  .reply(200, (_, body) => ({ ...World, players: [{ uuid: body.uuid, name: body.name }] }))
  .put(`/worlds/${config.realmId}/open`)
  .reply(200, true)
  .put(`/worlds/${config.realmId}/close`)
  .reply(200, true)
  .get(`/worlds/${config.realmId}/slot/${config.slotId}/download`)
  .reply(200, JavaWorldDownload)
  .get(`/worlds/${config.realmId}/backups`)
  .times(2)
  .reply(200, Backups)
  .put(`/worlds/${config.realmId}/backups?backupId=${config.backupId}&clientSupportsRetries`)
  .reply(204)

describe('Java', () => {
  describe('getRealms', () => {
    it('should return an array of Realm objects', async () => {
      expect(await api.getRealms()).to.deep.equal([World])
    })
  })
  describe('getRealm', () => {
    it('should return a Realm object', async () => {
      const realm = await api.getRealm(config.realmId)
      expect(realm).to.deep.equal(World)
    })
  })
  describe('restoreRealmFromBackup', () => {
    it('should return void', async () => {
      await api.restoreRealmFromBackup(config.realmId, config.backupId)
    })
  })
  describe('Realm getAddress', () => {
    it('should return an object containing the Realms address', async () => {
      const realm = await api.getRealm(config.realmId)
      expect(await realm.getAddress()).to.deep.equal({ host: '0.0.0.0', port: 19132 })
    })
  })
  describe('Realm InvitePayer', () => {
    it('should contain the player uuid, name and realmId included in the request', async () => {
      const realm = await api.getRealm(config.realmId)
      expect(await realm.invitePlayer(config.uuid, config.name)).to.deep.equal({ ...World, players: [{ uuid: config.uuid, name: config.name }] })
    })
  })
  describe('Realm Open', () => {
    it('should return true indicating Realm is now open', async () => {
      const realm = await api.getRealm(config.realmId)
      expect(await realm.open()).to.deep.equal(true)
    })
  })
  describe('Realm Close', () => {
    it('should return true indicating Realm is now closed', async () => {
      const realm = await api.getRealm(config.realmId)
      expect(await realm.close()).to.deep.equal(true)
    })
  })
  describe('Realm getBackups', () => {
    it('should return an array of backup objects', async () => {
      const realm = await api.getRealm(config.realmId)
      const backups = await realm.getBackups()
      expect(backups).to.deep.equal(Backups.backups.map(e => new Backup(null, null, e)))
    })
    it('should error when trying to download a backup', async () => {
      const realm = await api.getRealm(config.realmId)
      const backups = await realm.getBackups()
      await expect(backups[0].getDownload()).to.be.rejectedWith('Indiviual backup downloads is not a feature of Java Realms API, only getRealmWorldDownload() is available')
    })
  })
  describe('Realm getWorldDownload', () => {
    it('should return a world download object', async () => {
      const realm = await api.getRealm(config.realmId)
      expect(await realm.getWorldDownload()).to.deep.equal(new Download({ platform: 'java' }, JavaWorldDownload))
    })
  })
})
