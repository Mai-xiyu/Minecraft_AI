const debug = require('debug')('prismarine-auth')
const crypto = require('crypto')

const { Endpoints, fetchOptions } = require('../common/Constants')
const { checkStatus } = require('../common/Util')

const reportLimits = {
  maxOpinionCommentsLength: 1000,
  maxReportedMessageCount: 4,
  maxEvidenceMessageCount: 40,
  leadingContextMessageCount: 9,
  trailingContextMessageCount: 0
}

const reportReasons = {
  FALSE_REPORTING: 2,
  HATE_SPEECH: 5,
  TERRORISM_OR_VIOLENT_EXTREMISM: 16,
  CHILD_SEXUAL_EXPLOITATION_OR_ABUSE: 17,
  IMMINENT_HARM: 18,
  NON_CONSENSUAL_INTIMATE_IMAGERY: 19,
  HARASSMENT_OR_BULLYING: 21,
  DEFAMATION_IMPERSONATION_FALSE_INFORMATION: 27,
  SELF_HARM_OR_SUICIDE: 31,
  ALCOHOL_TOBACCO_DRUGS: 39
}

const toDER = pem => pem.split('\n').slice(1, -1).reduce((acc, cur) => Buffer.concat([acc, Buffer.from(cur, 'base64')]), Buffer.alloc(0))

class MinecraftJavaTokenManager {
  constructor (cache) {
    this.cache = cache
  }

  async getCachedAccessToken () {
    const { mca: token } = await this.cache.getCached()
    debug('[mc] token cache', token)
    if (!token) return
    const expires = token.obtainedOn + (token.expires_in * 1000)
    const remaining = expires - Date.now()
    const valid = remaining > 1000
    return { valid, until: expires, token: token.access_token, data: token }
  }

  async setCachedAccessToken (data) {
    await this.cache.setCachedPartial({
      mca: {
        ...data,
        obtainedOn: Date.now()
      }
    })
  }

  async verifyTokens () {
    const at = await this.getCachedAccessToken()
    if (!at || this.forceRefresh) {
      return false
    }
    debug('[mc] have user access token', at)
    if (at.valid) {
      return true
    }
    return false
  }

  async getAccessToken (xsts) {
    debug('[mc] authing to minecraft', xsts)
    const MineServicesResponse = await fetch(Endpoints.MinecraftServicesLogWithXbox, {
      method: 'post',
      ...fetchOptions,
      body: JSON.stringify({ identityToken: `XBL3.0 x=${xsts.userHash};${xsts.XSTSToken}` })
    }).then(checkStatus)

    debug('[mc] mc auth response', MineServicesResponse)
    await this.setCachedAccessToken(MineServicesResponse)
    return MineServicesResponse.access_token
  }

  async fetchProfile (accessToken) {
    debug(`[mc] fetching minecraft profile with ${accessToken.slice(0, 16)}`)
    const headers = { ...fetchOptions.headers, Authorization: `Bearer ${accessToken}` }
    const profile = await fetch(Endpoints.MinecraftServicesProfile, { headers })
      .then(checkStatus)
    debug(`[mc] got profile response: ${profile}`)
    return profile
  }

  /**
 * Fetches any product licenses attached to this accesstoken
 * @param {string} accessToken
 * @returns {object}
 */
  async fetchEntitlements (accessToken) {
    debug(`[mc] fetching entitlements with ${accessToken.slice(0, 16)}`)
    const headers = { ...fetchOptions.headers, Authorization: `Bearer ${accessToken}` }
    const entitlements = await fetch(Endpoints.MinecraftServicesLicense + `?requestId=${crypto.randomUUID()}`, { headers }).then(checkStatus)
    debug(`[mc] got entitlement response: ${entitlements}`)
    return entitlements
  }

  async fetchCertificates (accessToken) {
    debug(`[mc] fetching key-pair with ${accessToken.slice(0, 16)}`)
    const headers = { ...fetchOptions.headers, Authorization: `Bearer ${accessToken}` }
    const cert = await fetch(Endpoints.MinecraftServicesCertificate, { method: 'post', headers }).then(checkStatus)
    debug('[mc] got key-pair')
    const profileKeys = {
      publicPEM: cert.keyPair.publicKey,
      privatePEM: cert.keyPair.privateKey,
      publicDER: toDER(cert.keyPair.publicKey),
      privateDER: toDER(cert.keyPair.privateKey),
      signature: Buffer.from(cert.publicKeySignature, 'base64'),
      signatureV2: Buffer.from(cert.publicKeySignatureV2, 'base64'),
      expiresOn: new Date(cert.expiresAt),
      refreshAfter: new Date(cert.refreshedAfter)
    }
    profileKeys.public = crypto.createPublicKey({ key: profileKeys.publicDER, format: 'der', type: 'spki' })
    profileKeys.private = crypto.createPrivateKey({ key: profileKeys.privateDER, format: 'der', type: 'pkcs8' })
    return { profileKeys }
  }

  async reportPlayerChat (report) {
    const accessToken = await this.getCachedAccessToken()
    const headers = { ...fetchOptions.headers, Authorization: `Bearer ${accessToken}` }
    const createdTime = report.time || Date.now()
    const id = report.id || Date.now()
    const reportedMessagesCount = report.message.reduce((acc, cur) => { acc += (cur.reported ? 1 : 0); return acc }, 0)

    // Some basic client-side sanity checks to replicate vanilla behavior as server does not explain errors
    if (report.comments > reportLimits.maxOpinionCommentsLength) throw Error(`Report comment is too long, max allowed length is ${reportLimits.maxOpinionCommentsLength}`)
    if (!report.messages.length) throw Error('No messages were provided as evidence for report')
    if (report.messages.length > reportLimits.report.maxEvidenceMessageCount) throw Error(`Too many messages provided as evidence, max allowed is ${reportLimits.maxEvidenceMessageCount}`)
    if (reportedMessagesCount > reportLimits.maxReportedMessageCount) throw Error(`Too many reported messages, max allowed is ${reportLimits.maxReportedMessageCount}`)
    if (!report.reason) throw Error('Report reason was not specified')
    if (!(report.reason in reportReasons)) throw Error(`Invalid report reason: ${report.reason}`)

    const body = {
      id,
      report: {
        reason: report.reason,
        opinionComments: report.comments,
        evidence: report.messages.map(e => {
          return {
            header: {
              signatureOfPreviousHeader: e.previousHeaderSignature,
              profileId: e.uuid,
              hashOfBody: e.hash,
              signature: e.signature
            },
            body: e.timestamp
              ? {
                  timestamp: e.timestamp,
                  salt: e.salt,
                  lastSeenSignatures: e.lastSeen.map(m => ({
                    profileId: m.uuid,
                    lastSignature: m.signature
                  })),
                  message: e.message
                }
              : null,
            overridenMessage: e.originalMessage, // if it was modified by the server, ChatTrustLevel.java
            messageReported: e.reported
          }
        }),
        reportedEntity: {
          profileId: report.reportedPlayer
        },
        createdTime
      },
      clientInfo: {
        clientVersion: report.clientVersion
      },
      thirdPartyServerInfo: {
        address: report.serverAddress
      },
      realmInfo: report.realmInfo
    }

    debug('[mc] reporting player with payload', body)
    const reportResponse = await fetch(Endpoints.MinecraftServicesReport, { method: 'post', headers, body }).then(checkStatus)
    debug('[mc] server response for report', reportResponse)
    return true
  }
}
module.exports = MinecraftJavaTokenManager
