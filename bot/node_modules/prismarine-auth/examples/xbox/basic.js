const { Authflow } = require('prismarine-auth')
// No parameters needed - will login as Minecraft by default unless a custom Azure client ID is passed (see ./azure.js)
const flow = new Authflow()
module.exports = flow.getXboxToken().then(console.log)
