import { useEffect, useState } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import { Editor } from './components/Editor/Editor'
import { Sidebar } from './components/Sidebar/Sidebar'
import { PropertiesPanel } from './components/Properties/PropertiesPanel'
import { Toolbar } from './components/Toolbar/Toolbar'
import { SimulationPanel } from './components/Simulation/SimulationPanel'
import { ToastContainer } from './components/Toast/Toast'
import { useUIStore } from './store/uiStore'

import '@xyflow/react/dist/style.css'

function App() {
  const { showProperties, showSimulation, sidebarCollapsed, toggleSidebar } = useUIStore()
  const [isMobile, setIsMobile] = useState(false)

  // Check for mobile screen size and auto-collapse panels
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768
      setIsMobile(mobile)
      // Auto-collapse sidebar on mobile on first load
      if (mobile && !sidebarCollapsed) {
        toggleSidebar()
      }
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  return (
    <ReactFlowProvider>
      <div className="flex flex-col h-screen bg-editor-bg">
        {/* Top Toolbar */}
        <Toolbar />

        {/* Main Content Area */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar - Block Library */}
          <Sidebar />

          {/* Center - Block Diagram Editor */}
          <div className="flex-1 flex flex-col min-w-0">
            <Editor />
          </div>

          {/* Right Panel - Properties (collapsible) - hidden on mobile by default */}
          {showProperties && !isMobile && <PropertiesPanel />}
        </div>

        {/* Floating Simulation Results Panel */}
        {showSimulation && <SimulationPanel />}

        {/* Toast Notifications */}
        <ToastContainer />
      </div>
    </ReactFlowProvider>
  )
}

export default App
