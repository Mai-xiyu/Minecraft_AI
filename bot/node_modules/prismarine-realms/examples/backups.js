const { Authflow } = require('prismarine-auth')
const { RealmAPI } = require('prismarine-realms')

const [, , platform] = process.argv

if (!platform) {
  console.log('Usage: node backups.js <platform>')
  process.exit(1)
}

const authflow = new Authflow()

const api = RealmAPI.from(authflow, platform)

const main = async () => {
  const [realm] = await api.getRealms()

  const [latestBackup] = await realm.getBackups()

  latestBackup.getDownload().then(e => e.writeToDirectory('./examples'))
}

main()
