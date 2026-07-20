import { fireEvent, render, screen } from '@testing-library/react'
import { createElement } from 'react'
import { describe, expect, it, vi } from 'vitest'
import {
  calculateDragPosition,
  calculateResize,
  useDraggableWindow,
  type ResizeDirection,
  type UseDraggableWindowOptions,
} from './useDraggableWindow'

const defaultOptions: UseDraggableWindowOptions = {
  position: { x: 100, y: 100 },
  size: { width: 500, height: 400 },
  minSize: { width: 300, height: 200 },
  onFocus: vi.fn(),
  onPositionChange: vi.fn(),
  onSizeChange: vi.fn(),
}

function Harness({
  options,
  direction = 'se',
}: {
  options: UseDraggableWindowOptions
  direction?: ResizeDirection
}) {
  const windowInteraction = useDraggableWindow(options)
  return createElement(
    'div',
    null,
    createElement(
      'div',
      {
        'data-testid': 'drag-handle',
        'data-dragging': String(windowInteraction.isDragging),
        ...windowInteraction.dragHandleProps,
      },
      createElement('button', { type: 'button' }, 'Action')
    ),
    createElement('div', {
      'data-testid': 'resize-handle',
      'data-resizing': String(windowInteraction.isResizing),
      ...windowInteraction.getResizeHandleProps(direction),
    })
  )
}

function makeOptions(overrides: Partial<UseDraggableWindowOptions> = {}) {
  return {
    ...defaultOptions,
    onFocus: vi.fn(),
    onPositionChange: vi.fn(),
    onSizeChange: vi.fn(),
    ...overrides,
  }
}

describe('window interaction calculations', function () {
  it('moves from the starting pointer and clamps to the visible viewport bounds', function () {
    const interaction = {
      kind: 'drag' as const,
      pointerStart: { x: 120, y: 130 },
      positionStart: { x: 100, y: 100 },
    }

    expect(calculateDragPosition({ x: 220, y: 230 }, interaction, {
      width: 1000,
      height: 800,
    })).toEqual({ x: 200, y: 200 })
    expect(calculateDragPosition({ x: -500, y: -500 }, interaction, {
      width: 1000,
      height: 800,
    })).toEqual({ x: 0, y: 50 })
    expect(calculateDragPosition({ x: 2000, y: 2000 }, interaction, {
      width: 1000,
      height: 800,
    })).toEqual({ x: 900, y: 750 })
  })

  it('resizes all edges and corners while moving north and west origins', function () {
    const base = {
      kind: 'resize' as const,
      pointerStart: { x: 200, y: 200 },
      positionStart: { x: 100, y: 100 },
      sizeStart: { width: 500, height: 400 },
    }
    const minimum = { width: 300, height: 200 }

    expect(calculateResize({ x: 250, y: 260 }, { ...base, direction: 'se' }, minimum))
      .toEqual({ position: { x: 100, y: 100 }, size: { width: 550, height: 460 } })
    expect(calculateResize({ x: 150, y: 140 }, { ...base, direction: 'nw' }, minimum))
      .toEqual({ position: { x: 50, y: 40 }, size: { width: 550, height: 460 } })
    expect(calculateResize({ x: 250, y: 140 }, { ...base, direction: 'ne' }, minimum))
      .toEqual({ position: { x: 100, y: 40 }, size: { width: 550, height: 460 } })
    expect(calculateResize({ x: 150, y: 260 }, { ...base, direction: 'sw' }, minimum))
      .toEqual({ position: { x: 50, y: 100 }, size: { width: 550, height: 460 } })
  })

  it('enforces minimum dimensions without moving a constrained north or west edge', function () {
    const base = {
      kind: 'resize' as const,
      pointerStart: { x: 200, y: 200 },
      positionStart: { x: 100, y: 100 },
      sizeStart: { width: 500, height: 400 },
    }
    const minimum = { width: 300, height: 200 }

    expect(calculateResize({ x: -500, y: -500 }, { ...base, direction: 'se' }, minimum))
      .toEqual({ position: { x: 100, y: 100 }, size: minimum })
    expect(calculateResize({ x: 500, y: 500 }, { ...base, direction: 'nw' }, minimum))
      .toEqual({ position: { x: 100, y: 100 }, size: { width: 500, height: 400 } })
  })
})

describe('useDraggableWindow', function () {
  it('drags with a mouse until the pointer is released', function () {
    const options = makeOptions()
    render(createElement(Harness, { options }))
    const handle = screen.getByTestId('drag-handle')

    fireEvent.mouseDown(handle, { clientX: 120, clientY: 130 })
    expect(options.onFocus).toHaveBeenCalledOnce()
    expect(handle).toHaveAttribute('data-dragging', 'true')

    fireEvent.mouseMove(window, { clientX: 220, clientY: 230 })
    expect(options.onPositionChange).toHaveBeenCalledWith({ x: 200, y: 200 })

    fireEvent.mouseUp(window)
    expect(handle).toHaveAttribute('data-dragging', 'false')
    vi.mocked(options.onPositionChange).mockClear()
    fireEvent.mouseMove(window, { clientX: 300, clientY: 300 })
    expect(options.onPositionChange).not.toHaveBeenCalled()
  })

  it('does not drag when a title-bar button starts the event', function () {
    const options = makeOptions()
    render(createElement(Harness, { options }))

    fireEvent.mouseDown(screen.getByRole('button', { name: 'Action' }), {
      clientX: 120,
      clientY: 130,
    })
    fireEvent.mouseMove(window, { clientX: 220, clientY: 230 })

    expect(options.onFocus).not.toHaveBeenCalled()
    expect(options.onPositionChange).not.toHaveBeenCalled()
  })

  it('drags with touch input', function () {
    const options = makeOptions()
    render(createElement(Harness, { options }))
    const handle = screen.getByTestId('drag-handle')

    fireEvent.touchStart(handle, {
      touches: [{ clientX: 120, clientY: 130 }],
    })
    fireEvent.touchMove(window, {
      touches: [{ clientX: 220, clientY: 230 }],
    })

    expect(options.onPositionChange).toHaveBeenCalledWith({ x: 200, y: 200 })
    fireEvent.touchEnd(window)
    expect(handle).toHaveAttribute('data-dragging', 'false')
  })

  it('resizes with mouse input and reports size before position', function () {
    const options = makeOptions()
    const calls: string[] = []
    vi.mocked(options.onSizeChange).mockImplementation(function () { calls.push('size') })
    vi.mocked(options.onPositionChange).mockImplementation(function () { calls.push('position') })
    render(createElement(Harness, { options, direction: 'se' }))
    const handle = screen.getByTestId('resize-handle')

    expect(fireEvent.mouseDown(handle, { clientX: 200, clientY: 200 })).toBe(false)
    expect(handle).toHaveAttribute('data-resizing', 'true')
    fireEvent.mouseMove(window, { clientX: 250, clientY: 260 })

    expect(options.onSizeChange).toHaveBeenCalledWith({ width: 550, height: 460 })
    expect(options.onPositionChange).toHaveBeenCalledWith({ x: 100, y: 100 })
    expect(calls).toEqual(['size', 'position'])
    fireEvent.mouseUp(window)
  })

  it('resizes with touch input and cleans listeners up on unmount', function () {
    const options = makeOptions()
    const view = render(createElement(Harness, { options, direction: 'nw' }))
    const handle = screen.getByTestId('resize-handle')

    fireEvent.touchStart(handle, {
      touches: [{ clientX: 200, clientY: 200 }],
    })
    fireEvent.touchMove(window, {
      touches: [{ clientX: 150, clientY: 140 }],
    })

    expect(options.onSizeChange).toHaveBeenCalledWith({ width: 550, height: 460 })
    expect(options.onPositionChange).toHaveBeenCalledWith({ x: 50, y: 40 })

    vi.mocked(options.onSizeChange).mockClear()
    vi.mocked(options.onPositionChange).mockClear()
    view.unmount()
    fireEvent.touchMove(window, {
      touches: [{ clientX: 100, clientY: 100 }],
    })
    expect(options.onSizeChange).not.toHaveBeenCalled()
    expect(options.onPositionChange).not.toHaveBeenCalled()
  })
})
