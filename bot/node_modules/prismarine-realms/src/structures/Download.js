const fs = require('fs').promises
const fetch = require('node-fetch')

module.exports = class Download {
  #api
  constructor (api, data) {
    this.#api = api
    this.downloadUrl = data.downloadLink ?? data.downloadUrl
    if (this.#api.platform === 'bedrock') {
      this.token = data.token
      this.size = data.size
      this.fileExtension = '.mcworld'
    } else {
      this.resourcePackUrl = data.resourcePackUrl
      this.resourcePackHash = data.resourcePackHash
      this.fileExtension = '.tar.gz'
    }
  }

  async writeToDirectory (directory) {
    return this.#downloadWorld().then(buffer => fs.writeFile(`${directory}/world${this.fileExtension}`, buffer))
  }

  async getBuffer () {
    return this.#downloadWorld()
  }

  async #downloadWorld () {
    const res = await fetch(this.downloadUrl, {
      headers: (this.token) ? { Authorization: `Bearer ${this.token}` } : {}
    })

    if (!res.ok) throw new Error(`Failed to download world: ${res.status} ${res.statusText}`)

    return await res.buffer()
  }
}
