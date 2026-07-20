import { fireEvent, render } from '@testing-library/react'
import { useEffect } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { useDocumentMouseDrag } from './useDocumentMouseDrag'
function Harness({
  onMove,
  onEnd,
}: {
  onMove: (event: MouseEvent) => void
  onEnd: (event: MouseEvent) => void
}) {
  const startDrag = useDocumentMouseDrag()
  useEffect(() => {
    startDrag({ onMove, onEnd })
  }, [onEnd, onMove, startDrag])
  return <div />
}

describe('useDocumentMouseDrag', () => {
  it('forwards movement and ends exactly once', () => {
    const onMove = vi.fn()
    const onEnd = vi.fn()
    render(<Harness onMove={onMove} onEnd={onEnd} />)

    fireEvent.mouseMove(document, { clientX: 12, clientY: 34 })
    fireEvent.mouseUp(document)
    fireEvent.mouseMove(document)
    fireEvent.mouseUp(document)

    expect(onMove).toHaveBeenCalledOnce()
    expect(onEnd).toHaveBeenCalledOnce()
  })

  it('replaces an active drag and releases listeners on unmount', () => {
    const firstMove = vi.fn()
    const firstEnd = vi.fn()
    const secondMove = vi.fn()
    const secondEnd = vi.fn()
    const view = render(<Harness onMove={firstMove} onEnd={firstEnd} />)

    view.rerender(<Harness onMove={secondMove} onEnd={secondEnd} />)
    fireEvent.mouseMove(document)

    expect(firstMove).not.toHaveBeenCalled()
    expect(secondMove).toHaveBeenCalledOnce()
    view.unmount()
    fireEvent.mouseMove(document)
    fireEvent.mouseUp(document)
    expect(secondMove).toHaveBeenCalledOnce()
    expect(secondEnd).not.toHaveBeenCalled()
  })
})
