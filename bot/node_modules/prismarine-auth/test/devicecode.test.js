/* eslint-env mocha */
const chai = require('chai')
const chaiAsPromised = require('chai-as-promised')
const { Authflow, Titles } = require('../')
chai.use(chaiAsPromised)
const { expect } = chai

const crypto = require('crypto')
const curve = 'secp384r1'

describe('device code authentication', function () {
  this.timeout(4000)
  if (process.env.MSAL_CLIENT_ID) {
    // Non-MSAL will be tested in Minecraft Bedrock condition below
    it('should give us a token (MSAL)', (done) => {
      const onMsaCode = (code) => {
        if (!code) done(Error('missing user code'))
        if (code.userCode) done()
      }
      const flow = new Authflow('emailIdentifier@test.prismarine', './test', { flow: 'msal', authTitle: process.env.MSAL_CLIENT_ID }, onMsaCode)
      flow.getXboxToken().catch(done)
    })
  }

  it('should error if no certificate is present for bedrock', async () => {
    const flow = new Authflow('testauthflow', './test', { authTitle: Titles.MinecraftNintendoSwitch, flow: 'live' })
    await expect(flow.getMinecraftBedrockToken()).to.eventually.be.rejectedWith('Need to specifiy a ECDH x509 URL encoded public key')
  })
  it('should give us a token for bedrock', (done) => {
    const onMsaCode = (code) => {
      if (!code) done(Error('missing user code'))
      if (code.message) done()
    }

    const keypair = crypto.generateKeyPairSync('ec', { namedCurve: curve })
    const clientX509 = keypair.toString('base64')
    const flow = new Authflow('username', './test', { authTitle: Titles.MinecraftNintendoSwitch, flow: 'live' }, onMsaCode)
    flow.getMinecraftBedrockToken(clientX509).catch(done)
  })
})
