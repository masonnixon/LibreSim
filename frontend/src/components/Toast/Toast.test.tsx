import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act, cleanup, fireEvent } from '@testing-library/react'

// We need to reimport the module for each test suite to reset state
let ToastContainer: typeof import('./Toast').ToastContainer
let toast: typeof import('./Toast').toast
type ToastMessage = import('./Toast').ToastMessage

describe('Toast', () => {
  beforeEach(async () => {
    vi.useFakeTimers()
    // Reset the module to get fresh state
    vi.resetModules()
    const module = await import('./Toast')
    ToastContainer = module.ToastContainer
    toast = module.toast
  })

  afterEach(() => {
    vi.useRealTimers()
    cleanup()
  })

  describe('toast.show', () => {
    it('creates a success toast', () => {
      let receivedToasts: ToastMessage[] = []
      const unsubscribe = toast.subscribe((toasts) => {
        receivedToasts = toasts
      })

      toast.success('Success!', 'Operation completed')

      expect(receivedToasts.length).toBe(1)
      expect(receivedToasts[0].type).toBe('success')
      expect(receivedToasts[0].title).toBe('Success!')
      expect(receivedToasts[0].message).toBe('Operation completed')

      unsubscribe()
    })

    it('creates an info toast', () => {
      let receivedToasts: ToastMessage[] = []
      const unsubscribe = toast.subscribe((toasts) => {
        receivedToasts = toasts
      })

      toast.info('Info', 'Some information')

      expect(receivedToasts.length).toBe(1)
      expect(receivedToasts[0].type).toBe('info')

      unsubscribe()
    })

    it('creates a warning toast', () => {
      let receivedToasts: ToastMessage[] = []
      const unsubscribe = toast.subscribe((toasts) => {
        receivedToasts = toasts
      })

      toast.warning('Warning', 'Be careful')

      expect(receivedToasts.length).toBe(1)
      expect(receivedToasts[0].type).toBe('warning')

      unsubscribe()
    })

    it('creates toast with custom duration', () => {
      let receivedToasts: ToastMessage[] = []
      const unsubscribe = toast.subscribe((toasts) => {
        receivedToasts = toasts
      })

      toast.show('info', 'Custom', 'Custom duration', 1000)

      expect(receivedToasts[0].duration).toBe(1000)

      unsubscribe()
    })
  })

  describe('toast.dismiss', () => {
    it('removes a toast by id', () => {
      let receivedToasts: ToastMessage[] = []
      const unsubscribe = toast.subscribe((toasts) => {
        receivedToasts = toasts
      })

      toast.success('Test', 'Message')
      const toastId = receivedToasts[0].id

      toast.dismiss(toastId)

      expect(receivedToasts.length).toBe(0)

      unsubscribe()
    })
  })

  describe('toast.subscribe', () => {
    it('returns unsubscribe function', () => {
      const listener = vi.fn()
      const unsubscribe = toast.subscribe(listener)

      toast.success('Test', 'Message')
      expect(listener).toHaveBeenCalled()

      listener.mockClear()
      unsubscribe()

      toast.success('Another', 'Message')
      expect(listener).not.toHaveBeenCalled()
    })
  })

  describe('ToastContainer', () => {
    it('renders nothing when no toasts', () => {
      const { container } = render(<ToastContainer />)
      expect(container.querySelector('.toast-container')).toBeNull()
    })

    it('renders toasts when present', () => {
      render(<ToastContainer />)

      act(() => {
        toast.success('Test Title', 'Test Message')
      })

      expect(screen.getByText('Test Title')).toBeInTheDocument()
      expect(screen.getByText('Test Message')).toBeInTheDocument()
    })

    it('renders multiple toasts', () => {
      render(<ToastContainer />)

      act(() => {
        toast.success('First', 'First message')
        toast.info('Second', 'Second message')
        toast.warning('Third', 'Third message')
      })

      expect(screen.getByText('First')).toBeInTheDocument()
      expect(screen.getByText('Second')).toBeInTheDocument()
      expect(screen.getByText('Third')).toBeInTheDocument()
    })

    it('auto-dismisses toast after duration', () => {
      render(<ToastContainer />)

      act(() => {
        toast.success('Auto Dismiss', 'Will disappear', 1000)
      })

      expect(screen.getByText('Auto Dismiss')).toBeInTheDocument()

      act(() => {
        vi.advanceTimersByTime(1100)
      })

      expect(screen.queryByText('Auto Dismiss')).not.toBeInTheDocument()
    })

    it('uses default duration for success toast (4000ms)', () => {
      render(<ToastContainer />)

      act(() => {
        toast.success('SuccessToast', 'Default duration')
      })

      expect(screen.getByText('SuccessToast')).toBeInTheDocument()

      // Should still be there at 3900ms
      act(() => {
        vi.advanceTimersByTime(3900)
      })
      expect(screen.getByText('SuccessToast')).toBeInTheDocument()

      // Should be gone at 4100ms
      act(() => {
        vi.advanceTimersByTime(200)
      })
      expect(screen.queryByText('SuccessToast')).not.toBeInTheDocument()
    })

    it('uses default duration for warning toast (8000ms)', () => {
      render(<ToastContainer />)

      act(() => {
        toast.warning('WarningToast', 'Longer duration')
      })

      // Should still be there at 7900ms
      act(() => {
        vi.advanceTimersByTime(7900)
      })
      expect(screen.getByText('WarningToast')).toBeInTheDocument()

      // Should be gone at 8100ms
      act(() => {
        vi.advanceTimersByTime(200)
      })
      expect(screen.queryByText('WarningToast')).not.toBeInTheDocument()
    })

    it('dismisses toast on click', () => {
      render(<ToastContainer />)

      act(() => {
        toast.success('Click Me', 'To dismiss')
      })

      const toastElement = screen.getByText('Click Me').closest('.toast')
      expect(toastElement).toBeInTheDocument()

      act(() => {
        fireEvent.click(toastElement!)
      })

      expect(screen.queryByText('Click Me')).not.toBeInTheDocument()
    })

    it('applies correct CSS class based on type', () => {
      render(<ToastContainer />)

      act(() => {
        toast.success('Success Toast', 'msg')
        toast.info('Info Toast', 'msg')
        toast.warning('Warning Toast', 'msg')
      })

      const successToast = screen.getByText('Success Toast').closest('.toast')
      const infoToast = screen.getByText('Info Toast').closest('.toast')
      const warningToast = screen.getByText('Warning Toast').closest('.toast')

      expect(successToast?.className).toContain('toast-success')
      expect(infoToast?.className).toContain('toast-info')
      expect(warningToast?.className).toContain('toast-warning')
    })
  })
})
