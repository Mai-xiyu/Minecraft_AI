## History

### 1.3.2
* Retry 5xx errors with exponential backoff (@LucienHH)

### 1.3.1
* Use fs.promises over fs/promises (@extremeheat)

### 1.3.0
* import Authflow into index.d.ts (@jojomatik) [#35](https://github.com/PrismarineJS/prismarine-realms/pull/35)
* Add Realm backup & world download endpoints (@LucienHH) [#30](https://github.com/PrismarineJS/prismarine-realms/pull/30)
* Move docs to API.md (@LucienHH) [#24](https://github.com/PrismarineJS/prismarine-realms/pull/24)

### 1.2.0
* Fix typo in index.d.ts
* Add invite endpoints

### 1.1.1
* Fix missing debug dependency
* Retry 5 times for pc realm address endpoint

### 1.1.0

* Add getRealmFromInvite endpoint
* Add retry for server errors and getAddress return host/port
* Update doc and platform type handling

### 1.0.0

* initial implementation
