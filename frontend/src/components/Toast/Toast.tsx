import { useEffect, useState } from 'react'

export interface ToastMessage {
  id: string
  type: 'success' | 'info' | 'warning'
  title: string
  message: string
}

interface ToastProps {
  toast: ToastMessage
  onDismiss: (id: string) => void
}

function ToastItem({ toast, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id)
    }, 4000)
    return () => clearTimeout(timer)
  }, [toast.id, onDismiss])

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

export const toast = {
  show: (type: ToastMessage['type'], title: string, message: string) => {
    const newToast: ToastMessage = {
      id: Date.now().toString(),
      type,
      title,
      message,
    }
    currentToasts = [...currentToasts, newToast]
    toastListeners.forEach((listener) => listener(currentToasts))
  },
  success: (title: string, message: string) => toast.show('success', title, message),
  info: (title: string, message: string) => toast.show('info', title, message),
  warning: (title: string, message: string) => toast.show('warning', title, message),
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
