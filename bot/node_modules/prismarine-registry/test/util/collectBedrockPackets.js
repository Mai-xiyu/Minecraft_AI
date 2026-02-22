const bedrock = require('bedrock-protocol')
const { startServer } = require('minecraft-bedrock-server')
const debug = require('debug')('prismarine-registry')
const path = require('path')

async function collectPackets (version, names = ['start_game'], cb) {
  const collected = []
  const server = await new Promise((resolve) => {
    const server = startServer(version, () => resolve(server), {
      'online-mode': false,
      'server-port': 19130,
      path: path.join(__dirname, `server_bedrock_${version}`)
    })
  })

  console.log('Started server', version)

  const client = bedrock.createClient({
    version,
    host: '127.0.0.1',
    port: 19130,
    username: 'test',
    offline: true
  })

  let clientConnected = false

  client.on('join', () => {
    console.log('[client] Client connected')
    clientConnected = true
  })

  for (const name of names) {
    client.on(name, (packet) => {
      cb(name, packet)
      collected.push(packet)
    })
  }

  client.on('packet', ({ name }) => debug('[client] -> ', name))

  setTimeout(() => {
    console.log('Stopping server', version)
    server.kill()
    client.close()
    if (!clientConnected) {
      throw new Error('Client never connected')
    }
  }, 9000)
}

module.exports = collectPackets
