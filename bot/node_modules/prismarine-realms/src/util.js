function formatJavaAuth (res) {
  if (!res.profile?.id || !res.profile?.name) throw new Error('Failed to obtain profile data, does the authenticating account own minecraft?')
  return ['cookie', `sid=token:${res.token}:${res.profile.id}; user=${res.profile.name}; version=0.0.0`]
}

function formatBedrockAuth (res) {
  return ['authorization', `XBL3.0 x=${res.userHash};${res.XSTSToken}`]
}

module.exports = {
  formatJavaAuth,
  formatBedrockAuth
}
