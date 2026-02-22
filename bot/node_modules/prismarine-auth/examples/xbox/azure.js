const { Authflow } = require('prismarine-auth')

if (process.argv.length !== 5) {
  console.log('Usage: node azure.js <username> <cacheDirectory> <azureClientId>')
  process.exit(1)
}

const doAuth = () => {
  const flow = new Authflow(process.argv[2], process.argv[3], { authTitle: process.argv[4], flow: 'msal' })
  flow.getXboxToken().then(console.log)
}

doAuth()
