import { useEffect, useState } from 'react'

export interface ToastMessage {
  id: string
  type: 'success' | 'info' | 'warning'
  title: string
  message: string
  duration?: number // Duration in ms, undefined = use default
}

interface ToastProps {
  toast: ToastMessage
  onDismiss: (id: string) => void
}

// Default durations by type (in ms)
const DEFAULT_DURATIONS: Record<ToastMessage['type'], number> = {
  success: 4000,
  info: 5000,
  warning: 8000, // Warnings stay longer
}

function ToastItem({ toast, onDismiss }: ToastProps) {
  useEffect(() => {
    const duration = toast.duration ?? DEFAULT_DURATIONS[toast.type]
    const timer = setTimeout(() => {
      onDismiss(toast.id)
    }, duration)
    return () => clearTimeout(timer)
  }, [toast.id, toast.duration, toast.type, onDismiss])

  return (
    <div className={`toast toast-${toast.type}`} onClick={() => onDismiss(toast.id)}>
      <div className="font-medium text-sm">{toast.title}</div>
      <div className="text-xs text-gray-400 mt-1">{toast.message}</div>
    </div>
  )
}

// Toast store for global toast management
let toastListeners: ((toasts: ToastMessage[]) => void)[] = []
let currentToasts: ToastMessage[] = []
let toastCounter = 0

// eslint-disable-next-line react-refresh/only-export-components -- Global toast utility object used throughout the app
export const toast = {
  show: (type: ToastMessage['type'], title: string, message: string, duration?: number) => {
    const newToast: ToastMessage = {
      id: `${Date.now()}-${toastCounter++}`,
      type,
      title,
      message,
      duration,
    }
    currentToasts = [...currentToasts, newToast]
    toastListeners.forEach((listener) => listener(currentToasts))
  },
  success: (title: string, message: string, duration?: number) => toast.show('success', title, message, duration),
  info: (title: string, message: string, duration?: number) => toast.show('info', title, message, duration),
  warning: (title: string, message: string, duration?: number) => toast.show('warning', title, message, duration),
  dismiss: (id: string) => {
    currentToasts = currentToasts.filter((t) => t.id !== id)
    toastListeners.forEach((listener) => listener(currentToasts))
  },
  subscribe: (listener: (toasts: ToastMessage[]) => void) => {
    toastListeners.push(listener)
    return () => {
      toastListeners = toastListeners.filter((l) => l !== listener)
    }
  },
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  useEffect(() => {
    return toast.subscribe(setToasts)
  }, [])

  if (toasts.length === 0) return null

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={toast.dismiss} />
      ))}
    </div>
  )
}
