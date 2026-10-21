import { drawRig, isRigReady, loadRig, type RigAction } from './rig/nailongRig'

const canvas = document.getElementById('c') as HTMLCanvasElement
const context = canvas.getContext('2d')!
const rig = loadRig()

let mode: 'idle' | 'walk' | RigAction = new URLSearchParams(location.search).get('m') as never || 'walk'
let frozenAt: number | null = null

const nav = document.getElementById('nav')!
for (const name of ['idle', 'walk', 'send', 'play', 'feed', 'sleep']) {
  const button = document.createElement('button')
  button.textContent = name
  button.onclick = () => { mode = name as never; frozenAt = null }
  nav.appendChild(button)
}
const freeze = document.createElement('button')
freeze.textContent = 'congelar/seguir'
freeze.onclick = () => { frozenAt = frozenAt === null ? performance.now() : null }
nav.appendChild(freeze)

function loop(time: number) {
  context.imageSmoothingEnabled = false
  context.clearRect(0, 0, canvas.width, canvas.height)
  if (isRigReady(rig)) {
    context.save()
    context.translate(canvas.width / 2, canvas.height - 12)
    drawRig(context, rig, {
      time: frozenAt ?? time,
      walking: mode === 'walk',
      action: mode === 'idle' || mode === 'walk' ? null : (mode as RigAction),
      weak: false,
    })
    context.restore()
  }
  requestAnimationFrame(loop)
}
requestAnimationFrame(loop)
