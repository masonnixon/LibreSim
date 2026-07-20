import { useState, useEffect } from 'react'
import { useModelStore } from '../../store/modelStore'
import { useUIStore } from '../../store/uiStore'
import { exportModelAsMDL } from '../../utils/mdlExporter'
import { toast } from '../Toast/Toast'

type ExportFormat = 'json' | 'mdl'

export function SaveAsModal() {
  const { model, updateMetadata } = useModelStore()
  const { showSaveAsModal, closeSaveAsModal } = useUIStore()

  const [filename, setFilename] = useState('')
  const [format, setFormat] = useState<ExportFormat>('json')
  const [updateModelName, setUpdateModelName] = useState(true)

  // Sync filename with model name when modal opens
  useEffect(() => {
    if (showSaveAsModal && model) {
      setFilename(model.metadata.name || 'Untitled')
      setFormat('json')
      setUpdateModelName(true)
    }
  }, [showSaveAsModal, model])

  if (!showSaveAsModal || !model) return null

  const handleSave = () => {
    if (!filename.trim()) {
      toast.warning('Invalid Filename', 'Please enter a filename.')
      return
    }

    const cleanFilename = filename.trim()

    if (format === 'json') {
      // Export as JSON
      const modelToExport = updateModelName
        ? { ...model, metadata: { ...model.metadata, name: cleanFilename } }
        : model
      const dataStr = JSON.stringify(modelToExport, null, 2)
      const blob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(blob)

      const a = document.createElement('a')
      a.href = url
      a.download = `${cleanFilename}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast.success('Saved', `Exported as "${cleanFilename}.json"`)
    } else {
      // Export as MDL
      try {
        const modelToExport = updateModelName
          ? { ...model, metadata: { ...model.metadata, name: cleanFilename } }
          : model
        exportModelAsMDL(modelToExport, `${cleanFilename}.mdl`)
        toast.success('Saved', `Exported as "${cleanFilename}.mdl" (Simulink format)`)
      } catch (error) {
        console.error('Failed to export MDL:', error)
        toast.warning('Export Failed', `${error instanceof Error ? error.message : 'Unknown error'}`)
        return
      }
    }

    // Update only after the selected export completes successfully.
    if (updateModelName) {
      updateMetadata({ name: cleanFilename })
    }

    closeSaveAsModal()
  }

  const handleCancel = () => {
    closeSaveAsModal()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleCancel()
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSave()
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100]"
      onClick={handleCancel}
      onKeyDown={handleKeyDown}
    >
      <div
        className="bg-editor-surface border border-editor-border rounded-lg shadow-xl w-full max-w-md mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-editor-border">
          <h2 className="text-lg font-semibold">Save As</h2>
          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Filename */}
          <div>
            <label className="block text-sm mb-1">Filename</label>
            <input
              type="text"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              autoFocus
              className="w-full px-3 py-2 bg-editor-bg border border-editor-border rounded text-sm focus:outline-none focus:border-blue-500"
              placeholder="Enter filename"
            />
          </div>

          {/* Format Selection */}
          <div>
            <label className="block text-sm mb-2">Format</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="format"
                  value="json"
                  checked={format === 'json'}
                  onChange={() => setFormat('json')}
                  className="accent-blue-500"
                />
                <div>
                  <span className="text-sm">JSON</span>
                  <span className="text-xs text-gray-500 ml-1">(LibreSim native)</span>
                </div>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="format"
                  value="mdl"
                  checked={format === 'mdl'}
                  onChange={() => setFormat('mdl')}
                  className="accent-blue-500"
                />
                <div>
                  <span className="text-sm">MDL</span>
                  <span className="text-xs text-gray-500 ml-1">(Simulink)</span>
                </div>
              </label>
            </div>
          </div>

          {/* Update Model Name Option */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={updateModelName}
              onChange={(e) => setUpdateModelName(e.target.checked)}
              className="accent-blue-500"
            />
            <span className="text-sm text-gray-300">Update model name to match filename</span>
          </label>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 px-4 py-3 border-t border-editor-border">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-sm border border-editor-border rounded hover:bg-editor-border transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!filename.trim()}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  )
}
