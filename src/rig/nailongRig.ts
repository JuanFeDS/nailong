const PART_NAMES = [
  'head',
  'torso',
  'arm_near',
  'forearm_near',
  'arm_far',
  'forearm_far',
  'leg_near',
  'leg_far',
] as const

type PartName = (typeof PART_NAMES)[number]
export type RigImages = Record<PartName, HTMLImageElement>

export type RigAction = 'feed' | 'play' | 'sleep' | 'send' | null

interface Point {
  x: number
  y: number
}

export interface RigState {
  time: number
  walking: boolean
  action: RigAction
  weak: boolean
}

const PIVOT: Record<PartName, Point> = {
  head: { x: 29, y: 39 },
  torso: { x: 0, y: 0 },
  arm_near: { x: 12, y: 8 },
  arm_far: { x: 12, y: 8 },
  forearm_near: { x: 10, y: 4 },
  forearm_far: { x: 10, y: 4 },
  leg_near: { x: 14, y: 7 },
  leg_far: { x: 14, y: 7 },
}

const NECK: Point = { x: 46, y: 4 }
const SHOULDER_NEAR: Point = { x: 47, y: 10 }
const SHOULDER_FAR: Point = { x: 44, y: 9 }
const ELBOW: Point = { x: 11, y: 40 }
const HIP_NEAR: Point = { x: 31, y: 52 }
const HIP_FAR: Point = { x: 34, y: 52 }
const LEG_LENGTH = 48

const STEP_SPEED = 0.011
const LEG_SWING = 0.55
const ARM_SWING = 0.5

export function loadRig(): RigImages {
  const images = {} as RigImages
  for (const name of PART_NAMES) {
    const image = new Image()
    image.src = `/sprites/processed/parts/${name}.png`
    images[name] = image
  }
  return images
}

export function isRigReady(images: RigImages): boolean {
  return PART_NAMES.every((name) => images[name].complete && images[name].naturalWidth > 0)
}

const FAR_SHADE = 'brightness(0.82)'

function drawPart(
  context: CanvasRenderingContext2D,
  images: RigImages,
  name: PartName,
  joint: Point,
  angle: number,
  baseFilter: string,
  far = false,
) {
  context.save()
  context.filter = far ? `${baseFilter} ${FAR_SHADE}` : baseFilter
  context.translate(joint.x, joint.y)
  context.rotate(angle)
  context.drawImage(images[name], -PIVOT[name].x, -PIVOT[name].y)
  context.restore()
}

function drawArm(
  context: CanvasRenderingContext2D,
  images: RigImages,
  shoulder: Point,
  armAngle: number,
  forearmAngle: number,
  baseFilter: string,
  far: boolean,
) {
  const armName = far ? 'arm_far' : 'arm_near'
  const forearmName = far ? 'forearm_far' : 'forearm_near'
  context.save()
  context.filter = far ? `${baseFilter} ${FAR_SHADE}` : baseFilter
  context.translate(shoulder.x, shoulder.y)
  context.rotate(armAngle)
  context.translate(-PIVOT[armName].x, -PIVOT[armName].y)
  context.translate(ELBOW.x, ELBOW.y)
  context.rotate(forearmAngle)
  context.drawImage(images[forearmName], -PIVOT[forearmName].x, -PIVOT[forearmName].y)
  context.rotate(-forearmAngle)
  context.translate(-ELBOW.x, -ELBOW.y)
  context.drawImage(images[armName], 0, 0)
  context.restore()
}

export function drawRig(context: CanvasRenderingContext2D, images: RigImages, state: RigState) {
  const phase = state.time * STEP_SPEED
  const walking = state.walking && !state.action
  const swing = walking ? Math.sin(phase) : 0

  let legNear = swing * LEG_SWING
  let legFar = -swing * LEG_SWING
  let armNear = -swing * ARM_SWING + 0.1
  let armFar = swing * ARM_SWING + 0.1
  let forearmNear = 0.35 - Math.max(0, -swing) * 0.5
  let forearmFar = 0.35 - Math.max(0, swing) * 0.5
  let headAngle = 0
  let lift = walking ? Math.abs(Math.cos(phase)) * 3 : Math.sin(state.time / 450) * 0.8
  let liftNear = walking ? Math.max(0, -Math.cos(phase)) * 5 : 0
  let liftFar = walking ? Math.max(0, Math.cos(phase)) * 5 : 0

  if (state.action === 'send') {
    armNear = -2.5 + Math.sin(state.time / 110) * 0.35
    forearmNear = -0.4 + Math.sin(state.time / 110) * 0.3
  } else if (state.action === 'play') {
    const jump = Math.abs(Math.sin(state.time / 150))
    lift += jump * 10
    armNear = -2.2 + Math.sin(state.time / 100) * 0.3
    armFar = -2.2 - Math.sin(state.time / 100) * 0.3
    legNear = legFar = jump * 0.3
  } else if (state.action === 'feed') {
    const chew = Math.sin(state.time / 120)
    armNear = -1.4
    armFar = -1.4
    forearmNear = -1.3 + chew * 0.1
    forearmFar = -1.3 + chew * 0.1
    headAngle = 0.08 + chew * 0.04
  } else if (state.action === 'sleep') {
    headAngle = 0.25
    armNear = armFar = 0.05
    lift = Math.sin(state.time / 500) * 0.8
  }

  const baseFilter = state.weak ? 'saturate(0.45)' : 'none'
  context.save()
  context.translate(-HIP_NEAR.x, -(HIP_NEAR.y + LEG_LENGTH) - lift)

  drawArm(context, images, SHOULDER_FAR, armFar, forearmFar, baseFilter, true)

  drawPart(context, images, 'leg_far', { x: HIP_FAR.x, y: HIP_FAR.y - liftFar }, legFar, baseFilter, true)
  drawPart(context, images, 'leg_near', { x: HIP_NEAR.x, y: HIP_NEAR.y - liftNear }, legNear, baseFilter)

  context.filter = baseFilter
  context.drawImage(images.torso, 0, 0)
  drawPart(context, images, 'head', NECK, headAngle, baseFilter)

  drawArm(context, images, SHOULDER_NEAR, armNear, forearmNear, baseFilter, false)
  context.restore()
}
