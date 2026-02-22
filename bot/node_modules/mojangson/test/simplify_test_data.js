module.exports = [
  ['{}', {}],
  ['{key:value}', { key: 'value' }],
  ['{key:"value"}', { key: 'value' }],
  ['{key:"va,lue"}', { key: 'va,lue' }],
  ['{k1:v1,k2:v2}', { k1: 'v1', k2: 'v2' }],
  ['{number:0s}', { number: 0 }],
  ['{number:35.765d}', { number: 35.765 }],
  ['{number:35i}', { number: 35 }],
  ['{number:123b}', { number: 123 }],
  ['{nest:{}}', { nest: {} }],
  ['{nest:{nest:{}}}', { nest: { nest: {} } }],
  ['{id:35,Damage:5,Count:2,tag:{display:{Name:Testing}}}', {
    id: 35,
    Damage: 5,
    Count: 2,
    tag: { display: { Name: 'Testing' } }
  }],
  ['{id:"minecraft:dirt",Damage:0s,Count:1b}', { id: 'minecraft:dirt', Damage: 0, Count: 1 }],
  ['{key:value,}', { key: 'value' }],
  ['[0:v1,1:"v2",]', ['v1', 'v2']],
  // eslint-disable-next-line no-sparse-arrays
  ['[0:v1,2:v2]', ['v1', , 'v2']],
  ['[0:"§6Last Killed: None",1:"§6Last Killer: None",2:"§6Rank: §aNovice-III",3:"§6§6Elo Rating: 1000",]', ['§6Last Killed: None', '§6Last Killer: None', '§6Rank: §aNovice-III', '§6§6Elo Rating: 1000']],
  ['{id:1s,Damage:0s,Count:1b,tag:{display:{Name:"§r§6Class: Civilian",Lore:[0:"§6Last Killed: None",1:"§6Last Killer: None",2:"§6Rank: §aNovice-III",3:"§6§6Elo Rating: 1000",],},},}', {
    id: 1,
    Damage: 0,
    Count: 1,
    tag: {
      display: {
        Name: '§r§6Class: Civilian',
        Lore: ['§6Last Killed: None', '§6Last Killer: None', '§6Rank: §aNovice-III', '§6§6Elo Rating: 1000']
      }
    }
  }],
  ['[1,2,3]', [1, 2, 3]],
  ['[1,2,3,]', [1, 2, 3]],
  ['[]', []],
  ['["a","b;"]', ['a', 'b;']],
  ['{id:"minecraft:yello[w_shulker_box",Count:1b,tag:{BlockEntityTag:{CustomName:"Stacked Totems",x:0,y:0,z:0,id:"minecraft:shulker_box",Lock:""},display:{Name:"Stacked Totems"}},Damage:0s}', {
    id: 'minecraft:yello[w_shulker_box',
    Count: 1,
    tag: {
      BlockEntityTag: { CustomName: 'Stacked Totems', x: 0, y: 0, z: 0, id: 'minecraft:shulker_box', Lock: '' },
      display: { Name: 'Stacked Totems' }
    },
    Damage: 0
  }],
  // Int, Long and Byte arrays are not correctly simplified, see https://github.com/PrismarineJS/node-mojangson/pull/46
  ['[B;1b,2b,3b,]', { type: 'byte', value: [1, 2, 3] }],
  ['[I;1,2,3]', { type: 'int', value: [1, 2, 3] }],
  ['[L;1l,2l,3l]', { type: 'long', value: [1, 2, 3] }],
  ['{id:"§a"}', { id: '§a' }],
  ['{id:"a="}', { id: 'a=' }]
]
