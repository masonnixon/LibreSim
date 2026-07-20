// Behavioral coverage for the responsive application shell.
import { act, render, screen } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'

import App from './App'
import { useUIStore } from './store/uiStore'

vi.mock('react-plotly.js', function () {
  return { default: function PlotStub() { return null } }
})

const caseFn = it
const setupFn = beforeEach

function setViewport(width: number): void {
  Object.defineProperty(window, 'innerWidth', { configurable: true, value: width })
}

setupFn(function () {
  setViewport(1200)
  useUIStore.setState({ showProperties: true, sidebarCollapsed: false })
})

caseFn('keeps the sidebar collapsed across repeated mobile resize events', function () {
  const view = render(<App />)
  expect(screen.getByRole('heading', { name: 'Properties' })).toBeInTheDocument()

  setViewport(767)
  act(function () { window.dispatchEvent(new Event('resize')) })
  expect(screen.queryByRole('heading', { name: 'Properties' })).not.toBeInTheDocument()
  expect(useUIStore.getState().sidebarCollapsed).toBe(true)

  act(function () { window.dispatchEvent(new Event('resize')) })
  expect(useUIStore.getState().sidebarCollapsed).toBe(true)
  view.unmount()
})

caseFn('does not render the properties panel when it is disabled', function () {
  useUIStore.setState({ showProperties: false })
  const view = render(<App />)

  expect(screen.queryByRole('heading', { name: 'Properties' })).not.toBeInTheDocument()
  view.unmount()
})

caseFn('starts directly in the mobile layout', function () {
  setViewport(500)
  useUIStore.setState({ sidebarCollapsed: true })
  const view = render(<App />)

  expect(screen.queryByRole('heading', { name: 'Properties' })).not.toBeInTheDocument()
  expect(useUIStore.getState().sidebarCollapsed).toBe(true)
  view.unmount()
})
