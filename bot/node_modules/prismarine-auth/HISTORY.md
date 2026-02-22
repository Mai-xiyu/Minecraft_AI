## History

### 2.7.0
* [Add methods for fetching PlayFab and Minecraft Service tokens  (#107)](https://github.com/PrismarineJS/prismarine-auth/commit/1402f43dae29c8ffe65ffa2840b27542c06767ca) (thanks @LucienHH)

### 2.6.0
* [Bump mocha from 10.8.2 to 11.0.1 (#112)](https://github.com/PrismarineJS/prismarine-auth/commit/c5a13a05a34da8b9821c19eda900eca3543f89d3) (thanks @dependabot[bot])
* [Remove node-fetch in favor of the Node.js built-in fetch() function (#118)](https://github.com/PrismarineJS/prismarine-auth/commit/73634a7ea20ed20e9e7403bfd142534fd786179b) (thanks @extremeheat)

### 2.5.1
* [Remove jose dependency (#103)](https://github.com/PrismarineJS/prismarine-auth/commit/e70f42efddf01d4edeb3a3bb53c19cb76fd66ad0) (thanks @bluefoxy009)

### 2.5.0
* [Update mcpc endpoint for entitlements check (#101)](https://github.com/PrismarineJS/prismarine-auth/commit/d7ac3def2b9b9c14b2565581f4cf87f2f92fa188) (thanks @frej4189)
* [Add a forceRefresh option to Authflow (#100)](https://github.com/PrismarineJS/prismarine-auth/commit/01c826692494efaad5540446bd582e094a41fbd8) (thanks @extremeheat)
* [Add 3 MC authTitles (#99)](https://github.com/PrismarineJS/prismarine-auth/commit/b84c345770242d23ce35e8b943573936f86e4047) (thanks @w0ahL)

### 2.4.2
* [Fix CI, default to `live` over `msal` flow (#97)](https://github.com/PrismarineJS/prismarine-auth/commit/e693bcbc9123dd05fef77dc9032b0a8adad9f2df) (thanks @extremeheat)

### 2.4.1
* [Match Titles enum with exported Titles (#93)](https://github.com/PrismarineJS/prismarine-auth/commit/76e3f468bf78ada1c525d0aa9906df3f27e5c772) (thanks @LucienHH)

### 2.4.0
* [Add `forceRefresh` option to `getXboxToken` (#90)](https://github.com/PrismarineJS/prismarine-auth/commit/ac3e64e0eec408d9eeefa6b0bdcd11c30cef22be) (thanks @LucienHH)
* [Add URL with prefilled auth code to login message (#81)](https://github.com/PrismarineJS/prismarine-auth/commit/5cbe0e0a5157ae32c0a1ea531b295c2c9cd20783) (thanks @kairu82642)

### 2.3.0
* [Add command workflow (#75)](https://github.com/PrismarineJS/prismarine-auth/commit/a574e5acc72ac0499d1c3c146303468134b52307) (thanks @LucienHH)
* [Cache fixes (#73)](https://github.com/PrismarineJS/prismarine-auth/commit/85b66dc5bdd4b6ce9b763bdf18a79fa9ac3357c1) (thanks @LucienHH)
* [Bump @azure/msal-node from 1.18.1 to 2.0.2 (#72)](https://github.com/PrismarineJS/prismarine-auth/commit/a51a660f16abcd50830f08059128a8030cc7903e) (thanks @dependabot[bot])
* [Update caching doc for clarity](https://github.com/PrismarineJS/prismarine-auth/commit/9e967ca2942002881b4b3ca23cac567367f563a5) (thanks @extremeheat)

### 2.2.0
* Add mcpc chat report method

### 2.1.1
* Fix typings

### 2.1.0
*  include signatureV2 (@jtsiskin)

### 2.0.1
* Update docs

### 2.0.0
* BREAKING : Add flow option (#55) @LucienHH
  * `flow` argument now required to explicitly specify what authentication flow (alternative endpoints for authentication) to use when instantiating Authflow. Supported options are `live`, `msal`, `sisu` ; see documentation for more information. Set this to `msal` if you have an custom Azure client token or `live` if you want to login as a official Microsoft app (like vanilla Minecraft client). 

### 1.7.0
* Breaking: Abstract fetchCertificates in MinecraftJavaTokenManager (#52) 

### 1.6.0

* Add fetchCertificates option to getMinecraftJavaToken

### 1.5.4

* XboxTokenManager: Combine `getXSTSToken` & `getXSTSTokenWithTitle` and implement own `getUserToken` ([#47](https://github.com/PrismarineJS/prismarine-auth/pull/47))

### 1.5.3
* Fix web request error logging expecting JSON response @LucienHH
* Add exception messages for more Xbox API errors @Kashalls

### 1.5.2
* Don't log authentication prompt if codeCallback is specified. ([#40](https://github.com/PrismarineJS/prismarine-auth/pull/40)) - @ATXLtheAxolotl

### 1.5.1
* Update User-Agent header @LucienHH

### 1.5.0
* Move relyingParty option from constructor to `getXboxToken(relyingParty?: string)` ([#34](https://github.com/PrismarineJS/prismarine-auth/pull/34))
* Fixed a bug that would cause refreshing the MSA token to error due to an undefined function 

### 1.4.2
* add debug dependency (#31) - @safazi

### 1.4.1
* Correct missing await statement in live token refreshing (#29) - @dustinrue

### 1.4.0

* Allow to use a custom cache instead of using the filesystem only (#26) - @Paulomart
* Replace `fs.rmdirSync` with `fs.rmSync` (#25)
* Add `doSisuAuth` option (#24)

### 1.3.0
* Add `deviceType` and `deviceVersion` options to Authflow options [#21](https://github.com/PrismarineJS/prismarine-auth/pull/21)

### 1.2.1

* bump jose dep

### 1.2.0
* Improve error handling (#15)
* Fix caching, relyingParty issue (#13)
* Documentation updates, see [API usage](https://github.com/PrismarineJS/prismarine-auth/blob/master/docs/API.md).

### 1.1.2

* proper fix

### 1.1.1

* fix jose dep

### 1.1.0

* Added entitlement and profile checks for Minecraft Java Token
* Fixed bug when fetching only the xbox token
* Added examples
* Added index.d.ts

### 1.0.0

* initial implementation
