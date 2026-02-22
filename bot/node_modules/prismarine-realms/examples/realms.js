const { Authflow } = require('prismarine-auth')
const { RealmAPI } = require('prismarine-realms')

const [, , platform] = process.argv

if (!platform) {
  console.log('Usage: node realms.js <platform>')
  process.exit(1)
}

const authflow = new Authflow()

const api = RealmAPI.from(authflow, platform)

api.getRealms().then(console.log)
