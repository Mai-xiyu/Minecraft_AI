/* eslint-env mocha */

const { Physics, PlayerState } = require('prismarine-physics')
const { Vec3 } = require('vec3')
const expect = require('expect')

const mcData = require('minecraft-data')('1.13.2')
const Block = require('prismarine-block')('1.13.2')

const fakeWorld = {
  getBlock: (pos) => {
    const type = (pos.y < 60) ? mcData.blocksByName.stone.id : mcData.blocksByName.air.id
    const b = new Block(type, 0, 0)
    b.position = pos
    return b
  }
}

const fakeWallWorld = {
  getBlock: (pos) => {
    const type = (pos.y < 60 || pos.x > 50) ? mcData.blocksByName.stone.id : mcData.blocksByName.air.id
    const b = new Block(type, 0, 0)
    b.position = pos
    return b
  }
}

const fakeWebWorld = {
  getBlock: (pos) => {
    const type = (pos.y < 60) ? mcData.blocksByName.stone.id : mcData.blocksByName.cobweb.id
    const b = new Block(type, 0, 0)
    b.position = pos
    return b
  }
}

const waterWorld = {
  getBlock: (pos) => {
    const type = (pos.y < 60) ? mcData.blocksByName.water.id : mcData.blocksByName.air.id
    const b = new Block(type, 0, 0)
    b.position = pos
    return b
  }
}

const lavaWorld = {
  getBlock: (pos) => {
    const type = (pos.y < 60) ? mcData.blocksByName.lava.id : mcData.blocksByName.air.id
    const b = new Block(type, 0, 0)
    b.position = pos
    return b
  }
}

function fakePlayer (pos) {
  return {
    entity: {
      position: pos,
      velocity: new Vec3(0, 0, 0),
      onGround: false,
      isInWater: false,
      isInLava: false,
      isInWeb: false,
      isCollidedHorizontally: false,
      isCollidedVertically: false,
      elytraFlying: false,
      yaw: Math.PI * 3 / 2, // east (+x)
      pitch: 20 * Math.PI / 180,
      effects: {}
    },
    jumpTicks: 0,
    jumpQueued: false,
    fireworkRocketDuration: 0,
    version: '1.13.2',
    inventory: {
      slots: []
    }
  }
}

function untilIdle (player, physics, world, controls) {
  const playerState = new PlayerState(player, controls)
  while (!playerState.onGround || playerState.vel.x !== 0 || playerState.vel.z !== 0) {
    physics.simulatePlayer(playerState, world)
  }
  playerState.apply(player)
}

function passTicks (ticks, player, physics, world, controls) {
  const playerState = new PlayerState(player, controls)
  for (let i = 0; i < ticks; ++i) {
    physics.simulatePlayer(playerState, world)
  }
  playerState.apply(player)
}

function mpsToTps (mps) {
  // 20 ticks per second
  return mps / 20
}

describe('Elytra tests', () => {
  it('flies east and then back', () => {
    const physics = Physics(mcData, fakeWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 61, 0))
    player.inventory.slots[6] = { name: 'elytra' }

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.position).toEqual(new Vec3(0, 60, 0))

    // jump
    player.jumpQueued = true
    passTicks(10, player, physics, fakeWorld, controls)
    expect(player.entity.onGround).toBeFalsy()

    // fly
    player.entity.elytraFlying = true
    passTicks(1, player, physics, fakeWorld, controls)

    // boost
    player.fireworkRocketDuration = 20

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.elytraFlying).toBeFalsy()
    expect(player.fireworkRocketDuration).toEqual(0)

    expect(player.entity.position.x).toBeGreaterThan(140)
    expect(player.entity.position.y).toEqual(60)
    expect(player.entity.position.z).toBeCloseTo(0)

    // turn around
    player.entity.yaw = Math.PI / 2 // west (-x)

    // jump
    player.jumpQueued = true
    passTicks(10, player, physics, fakeWorld, controls)

    expect(player.entity.onGround).toBeFalsy()

    // fly
    player.entity.elytraFlying = true
    passTicks(1, player, physics, fakeWorld, controls)
    expect(player.entity.elytraFlying).toBeTruthy()

    // boost
    player.fireworkRocketDuration = 20

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.elytraFlying).toBeFalsy()
    expect(player.fireworkRocketDuration).toEqual(0)

    // should be back at start
    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.y).toEqual(60)
    expect(player.entity.position.z).toBeCloseTo(0)
  })

  it('flies south and then back', () => {
    const physics = Physics(mcData, fakeWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 61, 0))
    player.inventory.slots[6] = { name: 'elytra' }
    player.entity.yaw = 0 // north (-z)

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.position).toEqual(new Vec3(0, 60, 0))

    // jump
    player.jumpQueued = true
    passTicks(10, player, physics, fakeWorld, controls)
    expect(player.entity.onGround).toBeFalsy()

    // fly
    player.entity.elytraFlying = true
    passTicks(1, player, physics, fakeWorld, controls)

    // boost
    player.fireworkRocketDuration = 20

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.elytraFlying).toBeFalsy()
    expect(player.fireworkRocketDuration).toEqual(0)

    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.y).toEqual(60)
    expect(player.entity.position.z).toBeLessThan(-140)

    // turn around
    player.entity.yaw = Math.PI // south (z)

    // jump
    player.jumpQueued = true
    passTicks(10, player, physics, fakeWorld, controls)

    expect(player.entity.onGround).toBeFalsy()

    // fly
    player.entity.elytraFlying = true
    passTicks(1, player, physics, fakeWorld, controls)
    expect(player.entity.elytraFlying).toBeTruthy()

    // boost
    player.fireworkRocketDuration = 20

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.elytraFlying).toBeFalsy()
    expect(player.fireworkRocketDuration).toEqual(0)

    // should be back at start
    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.y).toEqual(60)
    expect(player.entity.position.z).toBeCloseTo(0)
  })

  it('flies north east and then back', () => {
    const physics = Physics(mcData, fakeWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 61, 0))
    player.inventory.slots[6] = { name: 'elytra' }
    // facing positive z, to the left is positive x
    player.entity.yaw = -Math.PI / 4 + 2 * Math.PI // right 45 degrees of north (-z), towards east (+x)

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.position).toEqual(new Vec3(0, 60, 0))

    // jump
    player.jumpQueued = true
    passTicks(10, player, physics, fakeWorld, controls)
    expect(player.entity.onGround).toBeFalsy()

    // fly
    player.entity.elytraFlying = true
    passTicks(1, player, physics, fakeWorld, controls)

    // boost
    player.fireworkRocketDuration = 20

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.elytraFlying).toBeFalsy()
    expect(player.fireworkRocketDuration).toEqual(0)

    expect(player.entity.position.x).toBeGreaterThan(140 * Math.sin(Math.PI / 4))
    expect(player.entity.position.y).toEqual(60)
    expect(player.entity.position.z).toBeLessThan(-140 * Math.sin(Math.PI / 4))

    // turn around
    player.entity.yaw = -Math.PI / 4 + Math.PI // south (z)

    // jump
    player.jumpQueued = true
    passTicks(10, player, physics, fakeWorld, controls)

    expect(player.entity.onGround).toBeFalsy()

    // fly
    player.entity.elytraFlying = true
    passTicks(1, player, physics, fakeWorld, controls)
    expect(player.entity.elytraFlying).toBeTruthy()

    // boost
    player.fireworkRocketDuration = 20

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.elytraFlying).toBeFalsy()
    expect(player.fireworkRocketDuration).toEqual(0)

    // should be back at start
    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.y).toEqual(60)
    expect(player.entity.position.z).toBeCloseTo(0)
  })

  it('stops flight without elytra', () => {
    const physics = Physics(mcData, fakeWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 80, 0))
    player.inventory.slots[6] = { name: 'elytra' }

    player.entity.elytraFlying = true
    player.fireworkRocketDuration = 20
    physics.simulatePlayer(new PlayerState(player, controls), fakeWorld).apply(player)
    expect(player.entity.elytraFlying).toBeTruthy()
    expect(player.fireworkRocketDuration).toEqual(19)
    player.inventory.slots[6] = undefined
    physics.simulatePlayer(new PlayerState(player, controls), fakeWorld).apply(player)
    expect(player.entity.elytraFlying).toBeFalsy()
    expect(player.fireworkRocketDuration).toEqual(0)
  })

  it('can fly out of water', () => {
    const physics = Physics(mcData, waterWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 40, 0))
    player.inventory.slots[6] = { name: 'elytra' }
    player.entity.pitch = 80 * Math.PI / 180

    player.entity.elytraFlying = true
    physics.simulatePlayer(new PlayerState(player, controls), waterWorld).apply(player)
    expect(player.entity.isInWater).toBeTruthy()
    expect(player.entity.elytraFlying).toBeTruthy()
    physics.simulatePlayer(new PlayerState(player, controls), waterWorld).apply(player)
    expect(player.entity.isInWater).toBeTruthy()
    expect(player.entity.elytraFlying).toBeTruthy()

    player.fireworkRocketDuration = 20
    physics.simulatePlayer(new PlayerState(player, controls), waterWorld).apply(player)
    expect(player.entity.elytraFlying).toBeTruthy()
    expect(player.fireworkRocketDuration).toEqual(19)

    const playerState = new PlayerState(player, controls)
    while (playerState.isInWater) {
      playerState.fireworkRocketDuration = 1
      physics.simulatePlayer(playerState, waterWorld)
    }
    playerState.apply(player)
    expect(player.fireworkRocketDuration).toEqual(0)
    expect(player.entity.position.y).toBeGreaterThan(59)
  })

  it('can fly out of lava', () => {
    const physics = Physics(mcData, lavaWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 40, 0))
    player.inventory.slots[6] = { name: 'elytra' }
    player.entity.pitch = 80 * Math.PI / 180

    player.entity.elytraFlying = true
    physics.simulatePlayer(new PlayerState(player, controls), lavaWorld).apply(player)
    expect(player.entity.isInLava).toBeTruthy()
    expect(player.entity.elytraFlying).toBeTruthy()
    physics.simulatePlayer(new PlayerState(player, controls), lavaWorld).apply(player)
    expect(player.entity.isInLava).toBeTruthy()
    expect(player.entity.elytraFlying).toBeTruthy()

    player.fireworkRocketDuration = 20
    physics.simulatePlayer(new PlayerState(player, controls), lavaWorld).apply(player)
    expect(player.entity.elytraFlying).toBeTruthy()
    expect(player.fireworkRocketDuration).toEqual(19)

    const playerState = new PlayerState(player, controls)
    while (playerState.isInLava) {
      playerState.fireworkRocketDuration = 1
      physics.simulatePlayer(playerState, lavaWorld)
    }
    playerState.apply(player)
    expect(player.fireworkRocketDuration).toEqual(0)
    expect(player.entity.position.y).toBeGreaterThan(59)
  })

  it('landing while jumping stops flight', () => {
    const physics = Physics(mcData, fakeWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 61, 0))
    player.inventory.slots[6] = { name: 'elytra' }

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)
    expect(player.entity.position).toEqual(new Vec3(0, 60, 0))

    // jump
    player.jumpQueued = true
    passTicks(10, player, physics, fakeWorld, controls)
    expect(player.entity.onGround).toBeFalsy()

    // fly
    player.entity.elytraFlying = true
    passTicks(1, player, physics, fakeWorld, controls)

    // boost
    player.fireworkRocketDuration = 20
    passTicks(10, player, physics, fakeWorld, controls)
    expect(player.entity.onGround).toBeFalsy()

    controls.jump = true
    const playerState = new PlayerState(player, controls)
    while (!playerState.onGround) {
      expect(playerState.elytraFlying).toBeTruthy()
      physics.simulatePlayer(playerState, fakeWorld)
    }
    playerState.apply(player)
    expect(player.entity.onGround).toBeTruthy()
    expect(player.entity.elytraFlying).toBeFalsy()

    // let jump controls cause a jump
    passTicks(10, player, physics, fakeWorld, controls)
    expect(player.entity.onGround).toBeFalsy()
    expect(player.entity.elytraFlying).toBeFalsy()
  })

  it('cant fly in webs', () => {
    const webPhysics = Physics(mcData, fakeWebWorld)
    const airPhysics = Physics(mcData, fakeWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const airPlayer = fakePlayer(new Vec3(0, 150, 0))
    airPlayer.inventory.slots[6] = { name: 'elytra' }
    airPlayer.entity.elytraFlying = true
    passTicks(20 * 10, airPlayer, airPhysics, fakeWorld, controls)

    const webPlayer = fakePlayer(new Vec3(0, 150, 0))
    webPlayer.inventory.slots[6] = { name: 'elytra' }
    webPlayer.entity.elytraFlying = true
    passTicks(20 * 10, webPlayer, webPhysics, fakeWebWorld, controls)

    // web player should have barely moved
    expect(webPlayer.entity.position.x).toBeGreaterThan(0)
    expect(webPlayer.entity.position.x).toBeLessThan(1)
    expect(webPlayer.entity.position.y).toBeGreaterThan(149)

    // elytra player should be far away and much lower
    expect(airPlayer.entity.position.x).toBeGreaterThan(200)
    expect(airPlayer.entity.position.y).toBeLessThan(110)
  })

  it('can hit a wall', () => {
    const physics = Physics(mcData, fakeWallWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 100, 0))
    player.inventory.slots[6] = { name: 'elytra' }
    player.entity.elytraFlying = true
    player.fireworkRocketDuration = 100

    // let bot accelerate from firework
    passTicks(10, player, physics, fakeWallWorld, controls)

    // should be moving 30 m/s (30 / 20 m/tick)
    expect(player.entity.velocity.x).toBeGreaterThan(mpsToTps(30))

    // until near wall
    const playerState = new PlayerState(player, controls)
    while (playerState.pos.x < 49) {
      physics.simulatePlayer(playerState, fakeWallWorld)
    }
    playerState.apply(player)

    // should still be moving fast
    expect(player.entity.velocity.x).toBeGreaterThan(mpsToTps(30))

    // 1 / (30/20) = 2/3, so 1 tick should be enough to hit the wall
    passTicks(1, player, physics, fakeWallWorld, controls)

    // it should have stopped in the x direction
    expect(player.entity.velocity.x).toBeCloseTo(0)
  })

  it('can flight straight up', () => {
    const physics = Physics(mcData, fakeWallWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 100, 0))
    player.inventory.slots[6] = { name: 'elytra' }
    player.entity.elytraFlying = true
    player.entity.pitch = Math.PI / 2
    player.fireworkRocketDuration = 20

    // let bot accelerate from firework
    passTicks(20, player, physics, fakeWallWorld, controls)

    // should be moving very fast
    expect(player.entity.velocity.y).toBeGreaterThan(mpsToTps(25))
    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.z).toBeCloseTo(0)

    passTicks(20, player, physics, fakeWallWorld, controls)
    expect(player.entity.velocity.y).toBeLessThan(mpsToTps(10))
    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.z).toBeCloseTo(0)

    passTicks(20, player, physics, fakeWallWorld, controls)
    expect(player.entity.velocity.y).toBeLessThan(0)
    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.z).toBeCloseTo(0)

    passTicks(20, player, physics, fakeWallWorld, controls)
    expect(player.entity.velocity.y).toBeLessThan(mpsToTps(20))
    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.z).toBeCloseTo(0)
  })

  it('can flight straight down', () => {
    const physics = Physics(mcData, fakeWallWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 1000, 0))
    player.inventory.slots[6] = { name: 'elytra' }
    player.entity.elytraFlying = true
    player.entity.pitch = -Math.PI / 2
    player.fireworkRocketDuration = 20

    // let bot accelerate from firework
    passTicks(200, player, physics, fakeWallWorld, controls)

    // should be moving very fast
    expect(player.entity.position.y).toBeGreaterThan(100)
    expect(player.entity.velocity.y).toBeLessThan(mpsToTps(-60))
    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.z).toBeCloseTo(0)

    // using firework actually slows the bot down
    player.fireworkRocketDuration = 20
    passTicks(10, player, physics, fakeWallWorld, controls)

    // should be slower now
    expect(player.entity.position.y).toBeGreaterThan(100)
    expect(player.entity.velocity.y).toBeGreaterThan(mpsToTps(-40))
    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.z).toBeCloseTo(0)
  })

  it('flies to point and then back', () => {
    const physics = Physics(mcData, fakeWorld)
    const controls = {
      forward: false,
      back: false,
      left: false,
      right: false,
      jump: false,
      sprint: false,
      sneak: false
    }
    const player = fakePlayer(new Vec3(0, 61, 0))
    player.inventory.slots[6] = { name: 'elytra' }

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.position).toEqual(new Vec3(0, 60, 0))

    const unNormedFacing = new Vec3(300, 60, 400)
    const facing = unNormedFacing.scale(1 / unNormedFacing.xzDistanceTo(new Vec3(0, 60, 0)))

    // yaw is facing north (-z) and rotating to the left, west (-z), so
    // atan2(-x, -z) is yaw
    const yaw = Math.atan2(-facing.x, -facing.z)
    player.entity.yaw = yaw

    // jump
    player.jumpQueued = true
    passTicks(10, player, physics, fakeWorld, controls)
    expect(player.entity.onGround).toBeFalsy()

    // fly
    player.entity.elytraFlying = true
    passTicks(1, player, physics, fakeWorld, controls)

    // boost
    player.fireworkRocketDuration = 20

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.elytraFlying).toBeFalsy()
    expect(player.fireworkRocketDuration).toEqual(0)

    facing.scale(player.entity.position.xzDistanceTo(new Vec3(0, 60, 0)))
    expect(player.entity.position.x).toBeCloseTo(facing.x)
    expect(player.entity.position.y).toBeCloseTo(60)
    expect(player.entity.position.z).toBeCloseTo(facing.z)

    // turn around
    player.entity.yaw += Math.PI

    // jump
    player.jumpQueued = true
    passTicks(10, player, physics, fakeWorld, controls)

    expect(player.entity.onGround).toBeFalsy()

    // fly
    player.entity.elytraFlying = true
    passTicks(1, player, physics, fakeWorld, controls)
    expect(player.entity.elytraFlying).toBeTruthy()

    // boost
    player.fireworkRocketDuration = 20

    // wait til on ground
    untilIdle(player, physics, fakeWorld, controls)

    expect(player.entity.elytraFlying).toBeFalsy()
    expect(player.fireworkRocketDuration).toEqual(0)

    // should be back at start
    expect(player.entity.position.x).toBeCloseTo(0)
    expect(player.entity.position.y).toEqual(60)
    expect(player.entity.position.z).toBeCloseTo(0)
  })
})
