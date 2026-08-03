import { useEffect, useRef, useState } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import { Editor } from './components/Editor/Editor'
import { Sidebar } from './components/Sidebar/Sidebar'
import { PropertiesPanel } from './components/Properties/PropertiesPanel'
import { Toolbar } from './components/Toolbar/Toolbar'
import { PlotWindowManager } from './components/Simulation/PlotWindowManager'
import { ToastContainer } from './components/Toast/Toast'
import { SettingsModal } from './components/Settings/SettingsModal'
import { HelpModal } from './components/Help/HelpModal'
import { useUIStore } from './store/uiStore'
import { makeReadyNotifier, type StartupState } from './startup'

import '@xyflow/react/dist/style.css'

interface AppProps {
  startup?: StartupState
}

function App({ startup = { embed: false } }: AppProps) {
  const { showProperties } = useUIStore()
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768)
  const notifyReady = useRef(makeReadyNotifier()).current

  // Check for mobile screen size and auto-collapse panels
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
      // Keep the sidebar collapsed while the viewport is mobile.
      if (mobile && !useUIStore.getState().sidebarCollapsed) {
        useUIStore.setState({ sidebarCollapsed: true })
      }
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  useEffect(() => {
    if (!startup.error) notifyReady(startup.example)
  }, [notifyReady, startup.error, startup.example])

  if (startup.error) {
    return (
      <div className="h-screen bg-editor-bg text-red-300 flex items-center justify-center p-6">
        {startup.error}
      </div>
    )
  }

  return (
    <ReactFlowProvider>
      <div className="flex flex-col h-screen bg-editor-bg">
        {/* Top Toolbar */}
        <Toolbar embed={startup.embed} restoreLastModel={!startup.example} />

        {/* Main Content Area */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar - Block Library */}
          {!startup.embed && <Sidebar />}

          {/* Center - Block Diagram Editor */}
          <div className="flex-1 flex flex-col min-w-0">
            <Editor />
          </div>

          {/* Right Panel - Properties (collapsible) - hidden on mobile by default */}
          {!startup.embed && showProperties && !isMobile && <PropertiesPanel />}
        </div>

        {/* Floating Plot Windows - one per scope block */}
        <PlotWindowManager />

        {/* Toast Notifications */}
        <ToastContainer />

        {/* Settings Modal */}
        <SettingsModal />

        {/* Help Modal */}
        <HelpModal />
      </div>
    </ReactFlowProvider>
  )
}

export default App
