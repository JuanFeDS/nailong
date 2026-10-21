import type { CSSProperties } from 'react'

interface Props {
  scale?: number
  frame?: number
  animate?: boolean
  sheet?: 'idle' | 'walk'
}

export function Sprite({ scale = 3, frame = 0, animate = false, sheet = 'idle' }: Props) {
  const style = { '--s': scale, '--frame': frame } as CSSProperties
  const classes = ['sprite']
  if (sheet === 'walk') classes.push('sprite--walk', 'sprite--walking')
  else if (animate) classes.push('sprite--idle')
  return <div className={classes.join(' ')} style={style} role="img" aria-label="Nailong" />
}
