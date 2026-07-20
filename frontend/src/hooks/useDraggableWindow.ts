import { useCallback, useEffect, useState } from 'react'
import type { MouseEvent as ReactMouseEvent, TouchEvent as ReactTouchEvent } from 'react'

export interface WindowPoint {
  x: number
  y: number
}

export interface WindowSize {
  width: number
  height: number
}

export type ResizeDirection = 'n' | 's' | 'e' | 'w' | 'ne' | 'nw' | 'se' | 'sw'

interface ViewportSize {
  width: number
  height: number
}

interface DragInteraction {
  kind: 'drag'
  pointerStart: WindowPoint
  positionStart: WindowPoint
}

interface ResizeInteraction {
  kind: 'resize'
  direction: ResizeDirection
  pointerStart: WindowPoint
  positionStart: WindowPoint
  sizeStart: WindowSize
}

type WindowInteraction = DragInteraction | ResizeInteraction
type StartEvent = ReactMouseEvent | ReactTouchEvent

export interface UseDraggableWindowOptions {
  position: WindowPoint
  size: WindowSize
  minSize: WindowSize
  onFocus: () => void
  onPositionChange: (position: WindowPoint) => void
  onSizeChange: (size: WindowSize) => void
}

export function calculateDragPosition(
  pointer: WindowPoint,
  interaction: DragInteraction,
  viewport: ViewportSize
): WindowPoint {
  const x = interaction.positionStart.x + pointer.x - interaction.pointerStart.x
  const y = interaction.positionStart.y + pointer.y - interaction.pointerStart.y

  return {
    x: Math.max(0, Math.min(viewport.width - 100, x)),
    y: Math.max(50, Math.min(viewport.height - 50, y)),
  }
}

export function calculateResize(
  pointer: WindowPoint,
  interaction: ResizeInteraction,
  minSize: WindowSize
): { position: WindowPoint; size: WindowSize } {
  const deltaX = pointer.x - interaction.pointerStart.x
  const deltaY = pointer.y - interaction.pointerStart.y
  let width = interaction.sizeStart.width
  let height = interaction.sizeStart.height
  let x = interaction.positionStart.x
  let y = interaction.positionStart.y

  if (interaction.direction.includes('e')) {
    width = Math.max(minSize.width, interaction.sizeStart.width + deltaX)
  }
  if (interaction.direction.includes('w')) {
    const possibleWidth = interaction.sizeStart.width - deltaX
    if (possibleWidth >= minSize.width) {
      width = possibleWidth
      x = interaction.positionStart.x + deltaX
    }
  }
  if (interaction.direction.includes('s')) {
    height = Math.max(minSize.height, interaction.sizeStart.height + deltaY)
  }
  if (interaction.direction.includes('n')) {
    const possibleHeight = interaction.sizeStart.height - deltaY
    if (possibleHeight >= minSize.height) {
      height = possibleHeight
      y = interaction.positionStart.y + deltaY
    }
  }

  return { position: { x, y }, size: { width, height } }
}

function getPointer(event: StartEvent | MouseEvent | TouchEvent): WindowPoint {
  if ('touches' in event) {
    return { x: event.touches[0].clientX, y: event.touches[0].clientY }
  }
  return { x: event.clientX, y: event.clientY }
}

export function useDraggableWindow({
  position,
  size,
  minSize,
  onFocus,
  onPositionChange,
  onSizeChange,
}: UseDraggableWindowOptions) {
  const [interaction, setInteraction] = useState<WindowInteraction | null>(null)

  const startDrag = useCallback(function (event: StartEvent) {
    if ((event.target as HTMLElement).closest('button')) return

    onFocus()
    setInteraction({
      kind: 'drag',
      pointerStart: getPointer(event),
      positionStart: position,
    })
  }, [onFocus, position])

  const startResize = useCallback(function (
    event: StartEvent,
    direction: ResizeDirection
  ) {
    event.preventDefault()
    event.stopPropagation()
    onFocus()
    setInteraction({
      kind: 'resize',
      direction,
      pointerStart: getPointer(event),
      positionStart: position,
      sizeStart: size,
    })
  }, [onFocus, position, size])

  useEffect(function () {
    if (!interaction) return
    const activeInteraction = interaction

    function move(event: MouseEvent | TouchEvent) {
      const pointer = getPointer(event)
      if (activeInteraction.kind === 'drag') {
        onPositionChange(calculateDragPosition(pointer, activeInteraction, {
          width: window.innerWidth,
          height: window.innerHeight,
        }))
        return
      }

      const next = calculateResize(pointer, activeInteraction, minSize)
      onSizeChange(next.size)
      onPositionChange(next.position)
    }

    function end() {
      setInteraction(null)
    }

    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', end)
    window.addEventListener('touchmove', move)
    window.addEventListener('touchend', end)

    return function cleanUpInteractionListeners() {
      window.removeEventListener('mousemove', move)
      window.removeEventListener('mouseup', end)
      window.removeEventListener('touchmove', move)
      window.removeEventListener('touchend', end)
    }
  }, [interaction, minSize, onPositionChange, onSizeChange])

  const getResizeHandleProps = useCallback(function (direction: ResizeDirection) {
    return {
      onMouseDown: function (event: ReactMouseEvent) {
        startResize(event, direction)
      },
      onTouchStart: function (event: ReactTouchEvent) {
        startResize(event, direction)
      },
    }
  }, [startResize])

  return {
    isDragging: interaction?.kind === 'drag',
    isResizing: interaction?.kind === 'resize',
    dragHandleProps: {
      onMouseDown: startDrag,
      onTouchStart: startDrag,
    },
    getResizeHandleProps,
  }
}
