import { useCallback, useEffect, useRef } from 'react'

interface MouseDragHandlers {
  onMove: (event: MouseEvent) => void
  onEnd: (event: MouseEvent) => void
}

export function useDocumentMouseDrag() {
  const activeRef = useRef<AbortController>()

  const cancelActive = useCallback(() => activeRef.current?.abort(), [])

  const startDrag = useCallback(
    ({ onMove, onEnd }: MouseDragHandlers) => {
      cancelActive()
      const controller = new AbortController()
      const finish = (event: MouseEvent) => {
        controller.abort()
        onEnd(event)
      }

      document.addEventListener('mousemove', onMove, {
        signal: controller.signal,
      })
      document.addEventListener('mouseup', finish, {
        signal: controller.signal,
      })
      activeRef.current = controller
    },
    [cancelActive]
  )

  useEffect(() => cancelActive, [cancelActive])
  return startDrag
}
