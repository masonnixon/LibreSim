import { useState, useEffect } from 'react'
import { useUIStore } from '../../store/uiStore'

// Keyboard shortcuts data
const shortcuts = {
  general: [
    { keys: 'Ctrl+S', action: 'Save model' },
    { keys: 'Ctrl+Z', action: 'Undo' },
    { keys: 'Ctrl+Y', action: 'Redo' },
    { keys: 'Ctrl+Shift+Z', action: 'Redo (alternative)' },
    { keys: 'Escape', action: 'Exit subsystem / Deselect' },
  ],
  editing: [
    { keys: 'Ctrl+A', action: 'Select all blocks' },
    { keys: 'Ctrl+C', action: 'Copy selected blocks' },
    { keys: 'Ctrl+V', action: 'Paste blocks' },
    { keys: 'Delete', action: 'Delete selected blocks' },
    { keys: 'Backspace', action: 'Delete selected blocks' },
  ],
  layout: [
    { keys: 'Space', action: 'Fit view to content' },
    { keys: 'Ctrl+R', action: 'Rotate selected blocks 90°' },
    { keys: 'Ctrl+]', action: 'Spread blocks apart (5%)' },
    { keys: 'Ctrl+[', action: 'Retract blocks closer (5%)' },
  ],
  navigation: [
    { keys: 'Mouse wheel', action: 'Zoom in/out' },
    { keys: 'Click + drag', action: 'Pan view' },
    { keys: 'Double-click subsystem', action: 'Enter subsystem' },
  ],
}

// About content (rendered as simple HTML-like structure)
const aboutContent = `
LibreSim is a web-based block diagram simulation tool inspired by Simulink, powered by the Object-oriented Simulation Kernel (OSK).

## Features

- **Visual Block Diagram Editor**: Drag-and-drop interface for building system models
- **Control Systems Focus**: Comprehensive library of blocks for control system design
- **Real-time Simulation**: Live visualization of simulation results with scopes and plots
- **Simulink Import/Export**: Import and export .mdl files for Simulink compatibility
- **Library Import**: Import MDL libraries as reusable subsystem blocks
- **Multiple Solvers**: RK4, Euler, and Merson's method ODE solvers
- **Undo/Redo**: Full history support for model editing

## Block Library

LibreSim includes 50+ blocks across categories:
- **Sources**: Constant, Step, Ramp, Sine Wave, Pulse, Clock, White Noise
- **Sinks**: Scope, Display, To Workspace, XY Graph
- **Continuous**: Integrator, Derivative, Transfer Function, State-Space, PID
- **Discrete**: Unit Delay, Zero-Order Hold, Discrete Integrator
- **Math**: Sum, Gain, Product, Abs, Trigonometry, Saturation
- **Signal Routing**: Mux, Demux, Switch
- **Signal Processing**: Filters, Rate Limiter, Backlash
- **Nonlinear**: Lookup Tables, Quantizer, Relay, Friction
- **Observers**: Kalman Filter, Luenberger Observer

## Solvers

| Solver | Order | Use Case |
|--------|-------|----------|
| Euler | 1st | Quick prototyping |
| RK4 | 4th | General purpose (default) |
| Merson | 4th | Stiff systems |

## Credits

Object-oriented Simulation Kernel (OSK) by Mason Nixon
Inspired by MathWorks Simulink
`

function ShortcutKey({ children }: { children: string }) {
  return (
    <kbd className="px-2 py-1 bg-editor-bg border border-editor-border rounded text-xs font-mono">
      {children}
    </kbd>
  )
}

function ShortcutRow({ keys, action }: { keys: string; action: string }) {
  return (
    <tr className="border-b border-editor-border/50">
      <td className="py-2 pr-4">
        <ShortcutKey>{keys}</ShortcutKey>
      </td>
      <td className="py-2 text-gray-300">{action}</td>
    </tr>
  )
}

function ShortcutsTab() {
  return (
    <div className="space-y-6">
      {/* General */}
      <div>
        <h3 className="text-sm font-semibold text-blue-400 uppercase mb-3">General</h3>
        <table className="w-full">
          <tbody>
            {shortcuts.general.map((s) => (
              <ShortcutRow key={s.keys} keys={s.keys} action={s.action} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Editing */}
      <div>
        <h3 className="text-sm font-semibold text-blue-400 uppercase mb-3">Selection & Editing</h3>
        <table className="w-full">
          <tbody>
            {shortcuts.editing.map((s) => (
              <ShortcutRow key={s.keys} keys={s.keys} action={s.action} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Layout */}
      <div>
        <h3 className="text-sm font-semibold text-blue-400 uppercase mb-3">View & Layout</h3>
        <table className="w-full">
          <tbody>
            {shortcuts.layout.map((s) => (
              <ShortcutRow key={s.keys} keys={s.keys} action={s.action} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Navigation */}
      <div>
        <h3 className="text-sm font-semibold text-blue-400 uppercase mb-3">Navigation</h3>
        <table className="w-full">
          <tbody>
            {shortcuts.navigation.map((s) => (
              <ShortcutRow key={s.keys} keys={s.keys} action={s.action} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function AboutTab() {
  // Simple markdown-like rendering
  const renderContent = (content: string) => {
    const lines = content.trim().split('\n')
    const elements: JSX.Element[] = []
    let inTable = false
    let tableRows: string[] = []

    const flushTable = () => {
      if (tableRows.length > 0) {
        const headerRow = tableRows[0]
        const dataRows = tableRows.slice(2) // Skip header separator
        const headers = headerRow.split('|').filter(Boolean).map(h => h.trim())

        elements.push(
          <table key={`table-${elements.length}`} className="w-full text-sm my-3 border-collapse">
            <thead>
              <tr className="border-b border-editor-border">
                {headers.map((h, i) => (
                  <th key={i} className="py-2 px-2 text-left text-gray-400 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dataRows.map((row, i) => {
                const cells = row.split('|').filter(Boolean).map(c => c.trim())
                return (
                  <tr key={i} className="border-b border-editor-border/50">
                    {cells.map((cell, j) => (
                      <td key={j} className="py-1.5 px-2 text-gray-300">{cell}</td>
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
        )
        tableRows = []
      }
    }

    lines.forEach((line, i) => {
      // Table detection
      if (line.startsWith('|')) {
        inTable = true
        tableRows.push(line)
        return
      } else if (inTable) {
        flushTable()
        inTable = false
      }

      // Headers
      if (line.startsWith('## ')) {
        elements.push(
          <h3 key={i} className="text-lg font-semibold text-blue-400 mt-4 mb-2">
            {line.slice(3)}
          </h3>
        )
        return
      }

      // Bold text with **
      if (line.includes('**')) {
        const parts = line.split(/\*\*([^*]+)\*\*/g)
        elements.push(
          <p key={i} className="text-gray-300 mb-2">
            {parts.map((part, j) =>
              j % 2 === 1 ? <strong key={j} className="text-white">{part}</strong> : part
            )}
          </p>
        )
        return
      }

      // List items
      if (line.startsWith('- ')) {
        elements.push(
          <p key={i} className="text-gray-300 ml-4 mb-1">
            <span className="text-blue-400 mr-2">•</span>
            {line.slice(2)}
          </p>
        )
        return
      }

      // Empty lines
      if (line.trim() === '') {
        elements.push(<div key={i} className="h-2" />)
        return
      }

      // Regular paragraphs
      elements.push(
        <p key={i} className="text-gray-300 mb-2">{line}</p>
      )
    })

    // Flush any remaining table
    flushTable()

    return elements
  }

  return (
    <div className="prose prose-invert max-w-none">
      {renderContent(aboutContent)}
    </div>
  )
}

export function HelpModal() {
  const { showHelpModal, helpModalTab, closeHelpModal, openHelpModal } = useUIStore()
  const [activeTab, setActiveTab] = useState<'shortcuts' | 'about'>(helpModalTab)

  // Sync tab with store when modal opens
  useEffect(() => {
    if (showHelpModal) {
      setActiveTab(helpModalTab)
    }
  }, [showHelpModal, helpModalTab])

  if (!showHelpModal) return null

  const handleClose = () => {
    closeHelpModal()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleClose()
    }
  }

  const handleTabChange = (tab: 'shortcuts' | 'about') => {
    setActiveTab(tab)
    openHelpModal(tab)
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100]"
      onClick={handleClose}
      onKeyDown={handleKeyDown}
    >
      <div
        className="bg-editor-surface border border-editor-border rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header with tabs */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-editor-border">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold">Help</h2>
            <div className="flex gap-1">
              <button
                onClick={() => handleTabChange('shortcuts')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  activeTab === 'shortcuts'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-editor-border'
                }`}
              >
                Shortcuts
              </button>
              <button
                onClick={() => handleTabChange('about')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  activeTab === 'about'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-editor-border'
                }`}
              >
                About
              </button>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1">
          {activeTab === 'shortcuts' ? <ShortcutsTab /> : <AboutTab />}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center px-4 py-3 border-t border-editor-border text-sm text-gray-500">
          <span>Press Escape to close</span>
          <a
            href="https://github.com/masonnixon/LibreSim"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 transition-colors"
          >
            View on GitHub
          </a>
        </div>
      </div>
    </div>
  )
}
