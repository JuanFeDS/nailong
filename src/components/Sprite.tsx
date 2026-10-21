import type { CSSProperties } from 'react'

interface Props {
  scale?: number
  frame?: number
  animate?: boolean
}

export function Sprite({ scale = 3, frame = 0, animate = false }: Props) {
  const style = { '--s': scale, '--frame': frame } as CSSProperties
  return <div className={animate ? 'sprite sprite--idle' : 'sprite'} style={style} role="img" aria-label="Nailong" />
}
