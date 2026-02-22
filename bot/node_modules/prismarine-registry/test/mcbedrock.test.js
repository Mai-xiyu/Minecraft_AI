/* eslint-env mocha */

const SUPPORTED_VERSIONS = ['1.17.10', '1.18.0', '1.18.11', '1.18.30', '1.19.1', '1.19.10']
const test = require('./mcbedrock')

describe('mcbedrock', function () {
  this.timeout(18000 * 10)

  for (const version of SUPPORTED_VERSIONS) {
    // skipped bedrock because it times out; fix in https://github.com/PrismarineJS/prismarine-registry/issues/43
    it.skip('works on ' + version, () => test(version))
  }
})
