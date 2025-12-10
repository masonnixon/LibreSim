import { ReactFlowProvider } from '@xyflow/react'
import { Editor } from './components/Editor/Editor'
import { Sidebar } from './components/Sidebar/Sidebar'
import { PropertiesPanel } from './components/Properties/PropertiesPanel'
import { Toolbar } from './components/Toolbar/Toolbar'
import { SimulationPanel } from './components/Simulation/SimulationPanel'
import { useUIStore } from './store/uiStore'

import '@xyflow/react/dist/style.css'

function App() {
  const { showProperties, showSimulation } = useUIStore()

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
          <div className="flex-1 flex flex-col">
            <Editor />

            {/* Bottom - Simulation Results (collapsible) */}
            {showSimulation && <SimulationPanel />}
          </div>

          {/* Right Panel - Properties (collapsible) */}
          {showProperties && <PropertiesPanel />}
        </div>
      </div>
    </ReactFlowProvider>
  )
}

export default App
