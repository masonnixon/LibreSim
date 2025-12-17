import { useModelStore } from '../../store/modelStore'
import { blockRegistry } from '../../blocks'

export function PropertiesPanel() {
  const { model, selectedBlockIds, updateBlockParameters, renameBlock, getCurrentBlocks } = useModelStore()

  // Get blocks at current path level (handles subsystem navigation)
  const currentBlocks = getCurrentBlocks()

  if (!model || selectedBlockIds.length === 0) {
    return (
      <div className="w-72 bg-editor-surface border-l border-editor-border p-4">
        <h2 className="font-semibold text-sm mb-4">Properties</h2>
        <p className="text-gray-400 text-sm">Select a block to view its properties</p>
      </div>
    )
  }

  if (selectedBlockIds.length > 1) {
    return (
      <div className="w-72 bg-editor-surface border-l border-editor-border p-4">
        <h2 className="font-semibold text-sm mb-4">Properties</h2>
        <p className="text-gray-400 text-sm">
          {selectedBlockIds.length} blocks selected
        </p>
      </div>
    )
  }

  // Find block in current view (works inside subsystems too)
  const block = currentBlocks.find((b) => b.id === selectedBlockIds[0])
  if (!block) return null

  // Get definition or create a fallback for unknown block types
  const registeredDef = blockRegistry.get(block.type)
  const definition = registeredDef || {
    type: block.type,
    category: 'math',
    name: block.name || block.type,
    description: `Block type: ${block.type}`,
    inputs: block.inputPorts.map((p) => ({ name: p.name, dataType: p.dataType || 'double', dimensions: p.dimensions || [1] })),
    outputs: block.outputPorts.map((p) => ({ name: p.name, dataType: p.dataType || 'double', dimensions: p.dimensions || [1] })),
    parameters: Object.keys(block.parameters || {}).map((key) => ({
      name: key,
      label: key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1'),
      type: typeof block.parameters[key] === 'number' ? 'number' : typeof block.parameters[key] === 'boolean' ? 'boolean' : 'string',
      default: block.parameters[key],
    })),
  }

  const handleParameterChange = (paramName: string, value: unknown) => {
    updateBlockParameters(block.id, { [paramName]: value })
  }

  return (
    <div className="w-72 bg-editor-surface border-l border-editor-border flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-editor-border">
        <h2 className="font-semibold text-sm mb-2">Properties</h2>
        <input
          type="text"
          value={block.name}
          onChange={(e) => renameBlock(block.id, e.target.value)}
          className="w-full px-2 py-1 bg-editor-bg border border-editor-border rounded text-sm focus:outline-none focus:border-blue-500"
        />
        <p className="text-xs text-gray-400 mt-1">{definition.description}</p>
      </div>

      {/* Parameters */}
      <div className="flex-1 overflow-y-auto p-4">
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-3">
          Parameters
        </h3>

        {definition.parameters.length === 0 ? (
          <p className="text-sm text-gray-400">No parameters</p>
        ) : (
          <div className="space-y-4">
            {definition.parameters.map((param) => (
              <div key={param.name}>
                <label className="block text-sm mb-1">{param.label}</label>
                {param.description && (
                  <p className="text-xs text-gray-400 mb-1">{param.description}</p>
                )}
                {renderParameterInput(param, block.parameters[param.name], (value) =>
                  handleParameterChange(param.name, value)
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Ports Info */}
      <div className="p-4 border-t border-editor-border">
        <h3 className="text-xs font-semibold text-gray-400 uppercase mb-2">
          Ports
        </h3>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-gray-400">Inputs:</span>{' '}
            {block.inputPorts.length}
          </div>
          <div>
            <span className="text-gray-400">Outputs:</span>{' '}
            {block.outputPorts.length}
          </div>
        </div>
      </div>
    </div>
  )
}

function renderParameterInput(
  param: { type: string; options?: { value: string; label: string }[]; min?: number; max?: number; step?: number },
  value: unknown,
  onChange: (value: unknown) => void
) {
  const baseInputClass =
    'w-full px-2 py-1 bg-editor-bg border border-editor-border rounded text-sm focus:outline-none focus:border-blue-500'

  switch (param.type) {
    case 'number':
      return (
        <input
          type="number"
          value={value as number}
          min={param.min}
          max={param.max}
          step={param.step ?? 0.01}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className={baseInputClass}
        />
      )

    case 'string':
      return (
        <input
          type="text"
          value={value as string}
          onChange={(e) => onChange(e.target.value)}
          className={baseInputClass}
        />
      )

    case 'boolean':
      return (
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={value as boolean}
            onChange={(e) => onChange(e.target.checked)}
            className="rounded border-editor-border bg-editor-bg"
          />
          <span className="text-sm">{value ? 'Enabled' : 'Disabled'}</span>
        </label>
      )

    case 'select':
      return (
        <select
          value={value as string}
          onChange={(e) => onChange(e.target.value)}
          className={baseInputClass}
        >
          {param.options?.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      )

    case 'array':
      return (
        <input
          type="text"
          value={JSON.stringify(value)}
          onChange={(e) => {
            try {
              onChange(JSON.parse(e.target.value))
            } catch {
              // Invalid JSON, ignore
            }
          }}
          className={baseInputClass}
          placeholder="[1, 2, 3]"
        />
      )

    default:
      return (
        <input
          type="text"
          value={String(value)}
          onChange={(e) => onChange(e.target.value)}
          className={baseInputClass}
        />
      )
  }
}
