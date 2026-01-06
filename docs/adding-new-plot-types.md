# Adding New Plot Types to LibreSim

This guide walks through all the steps required to add a new plot/visualization type to LibreSim. We use the 3D Scope implementation as a reference example.

## Overview

Adding a new plot type requires changes across the full stack:

1. **Backend OSK Block** - The simulation block that collects data
2. **Backend Registration** - Register the block in OSK and the adapter
3. **Backend Result Collection** - Ensure data flows to the frontend
4. **Frontend Block Definition** - Define the block for the editor
5. **Frontend Type Extensions** - Extend signal data types
6. **Frontend Plot Component** - Create the visualization component
7. **Frontend Routing** - Route signals to the correct component
8. **Code Generation** - Support for compiled simulations (optional)
9. **Example Model** - Create a demonstration example

---

## Step 1: Create the Backend OSK Block

Create a new block class in `backend/src/osk/blocks/sinks.py` (or appropriate category file).

### Key Requirements

- Inherit from `Block`
- Implement `init()`, `update()`, `rpt()`, `getData()`, `getOutput()`
- For multi-input blocks, use `input_blocks` list and `connectInput()` method
- Record data in `rpt()` when `State.ready` is true

### Example: Scope3D

```python
class Scope3D(Block):
    """3D Scope block - records X, Y, Z signals for 3D visualization."""

    def __init__(self, x_label="X", y_label="Y", z_label="Z", **kwargs):
        super().__init__()
        self.x_label = x_label
        self.y_label = y_label
        self.z_label = z_label
        self.inputs = [0.0, 0.0, 0.0]  # X, Y, Z
        self.input_blocks = [None, None, None]
        self.input_source_ports = [0, 0, 0]
        self.times = []
        self.x_values = []
        self.y_values = []
        self.z_values = []

    def init(self):
        """Clear recorded data at simulation start."""
        self.times = []
        self.x_values = []
        self.y_values = []
        self.z_values = []

    def setInput(self, value, port=0):
        """Set input value for a specific port."""
        if port < 3:
            self.inputs[port] = value

    def connectInput(self, block, port=0, source_port=0):
        """Connect an input block to a specific port."""
        if port < 3:
            self.input_blocks[port] = block
            self.input_source_ports[port] = source_port

    def update(self):
        """Read inputs from connected blocks."""
        for i, block in enumerate(self.input_blocks):
            if block is not None:
                source_port = self.input_source_ports[i]
                self.inputs[i] = block.getOutput(source_port)

    def rpt(self):
        """Record data when simulation is ready to report."""
        if State.ready:
            self.times.append(State.t)
            self.x_values.append(self.inputs[0])
            self.y_values.append(self.inputs[1])
            self.z_values.append(self.inputs[2])

    def getData(self):
        """Return recorded data for visualization."""
        return {
            "times": self.times,
            "x": self.x_values,
            "y": self.y_values,
            "z": self.z_values,
            "inputNames": [self.x_label, self.y_label, self.z_label],
        }

    def getOutput(self, port=0):
        """Return current input value (for chaining)."""
        if port < 3:
            return self.inputs[port]
        return 0.0
```

---

## Step 2: Register the Block in OSK

### 2.1 Export from `backend/src/osk/blocks/__init__.py`

```python
from .sinks import Scope3D

__all__ = [
    # ... existing exports
    "Scope3D",
]
```

### 2.2 Add to Block Map in `backend/src/simulation/osk_adapter.py`

Add the block type to `BLOCK_MAP`:

```python
BLOCK_MAP: dict[str, type[Block]] = {
    # ... existing blocks
    "scope_3d": Scope3D,
}
```

### 2.3 Add Parameter Mapping

Add parameter mappings in `PARAM_MAP`:

```python
PARAM_MAP: dict[str, dict[str, str]] = {
    # ... existing mappings
    "scope_3d": {"xLabel": "x_label", "yLabel": "y_label", "zLabel": "z_label"},
}
```

### 2.4 Track as Sink Block

Add the block type to the sink blocks tracking in `_create_osk_block()`:

```python
# Track sink blocks for output recording
if block_type in ["scope", "scope_3d", "display", "to_workspace"]:
    self._sink_blocks.append(compiled_block.id)
```

---

## Step 3: Handle Data Collection

For blocks that accumulate data internally (like 3D scope), you need special handling.

### 3.1 Add `get_scope_data()` Method to OSKAdapter

```python
def get_scope_data(self) -> list[dict[str, Any]]:
    """Get data from special scope blocks that accumulate data internally."""
    signals = []
    for block_id in self._sink_blocks:
        osk_block = self._osk_blocks.get(block_id)
        compiled_block = self._block_map.get(block_id)

        if not osk_block or not compiled_block:
            continue

        # Check if this is a Scope3D block (has getData with x, y, z)
        if hasattr(osk_block, "getData"):
            data = osk_block.getData()
            # 3D Scope: has x, y, z arrays
            if "x" in data and "y" in data and "z" in data:
                signals.append(
                    {
                        "blockId": block_id,
                        "portId": "out",
                        "name": compiled_block.name if compiled_block else block_id,
                        "times": data.get("times", []),
                        "x": data.get("x", []),
                        "y": data.get("y", []),
                        "z": data.get("z", []),
                        "inputNames": data.get("inputNames", ["X", "Y", "Z"]),
                        "is3D": True,  # Flag for frontend routing
                    }
                )
    return signals
```

### 3.2 Skip in `_record_outputs()`

For blocks that use `getData()`, skip them in the per-step recording:

```python
def _record_outputs(self) -> dict[str, float]:
    # ...
    for block_id in self._sink_blocks:
        # Skip Scope3D blocks - they accumulate data internally
        if compiled_block.type == "scope_3d":
            continue
        # ... rest of recording logic
```

### 3.3 Call from SimulationRunner

In `backend/src/simulation/runner.py`, add to `get_results()`:

```python
def get_results(self) -> dict[str, Any]:
    # ... existing signal collection

    # Collect data from special sink blocks
    signals.extend(self._adapter.get_scope_data())

    # ... rest of method
```

### 3.4 Handle Named Port Connections

If your block uses named input ports (like "x", "y", "z" instead of "in1", "in2"), add handling in `_setup_connections()`:

```python
# In the target port index parsing section:
elif suffix == "x":
    target_port_index = 0
elif suffix == "y":
    target_port_index = 1
elif suffix == "z":
    target_port_index = 2
```

---

## Step 4: Define Frontend Block

Add the block definition in `frontend/src/blocks/sinks.ts`:

```typescript
export const sinkBlocks: BlockDefinition[] = [
  // ... existing blocks
  {
    type: 'scope_3d',
    category: 'sinks',
    name: '3D Scope',
    description: 'Display 3D trajectory plot',
    inputs: [
      { name: 'x', dataType: 'double', dimensions: [1] },
      { name: 'y', dataType: 'double', dimensions: [1] },
      { name: 'z', dataType: 'double', dimensions: [1] },
    ],
    outputs: [],
    parameters: [
      {
        name: 'xLabel',
        type: 'string',
        default: 'X',
        label: 'X Axis Label',
      },
      {
        name: 'yLabel',
        type: 'string',
        default: 'Y',
        label: 'Y Axis Label',
      },
      {
        name: 'zLabel',
        type: 'string',
        default: 'Z',
        label: 'Z Axis Label',
      },
    ],
    icon: '📐',
  },
]
```

---

## Step 5: Extend Signal Data Types

In `frontend/src/types/simulation.ts`, extend `SignalData`:

```typescript
export interface SignalData {
  blockId: string
  portId: string
  name: string
  times: number[]
  values?: number[] | number[][]
  inputNames?: string[]
  numInputs?: number
  // 3D scope specific fields
  x?: number[]
  y?: number[]
  z?: number[]
  is3D?: boolean
}
```

---

## Step 6: Create the Plot Component

Create a new component in `frontend/src/components/Simulation/`.

### Example: Scope3DWindow.tsx

Key aspects:
- Accept `signal: SignalData` prop with your custom fields
- Use appropriate charting library (Plotly for 3D)
- Handle window dragging/resizing
- Support minimized state

```typescript
import Plot from 'react-plotly.js'

interface Scope3DWindowProps {
  blockId: string
  blockName: string
  signal: SignalData
  windowState: PlotWindowState
  zIndex: number
  onFocus: () => void
}

export function Scope3DWindow({ signal, ... }: Scope3DWindowProps) {
  const plotData = useMemo(() => {
    if (!signal.x || !signal.y || !signal.z) return []

    return [{
      type: 'scatter3d' as const,
      mode: 'lines' as const,
      x: signal.x,
      y: signal.y,
      z: signal.z,
      line: { color: '#89b4fa', width: 3 },
    }]
  }, [signal])

  return (
    <div className="...">
      <Plot
        data={plotData}
        layout={{
          scene: {
            xaxis: { title: signal.inputNames?.[0] || 'X' },
            yaxis: { title: signal.inputNames?.[1] || 'Y' },
            zaxis: { title: signal.inputNames?.[2] || 'Z' },
          },
        }}
      />
    </div>
  )
}
```

---

## Step 7: Route to the Component

In `frontend/src/components/Simulation/PlotWindowManager.tsx`:

### 7.1 Add to Block Type Detection

```typescript
function findAllScopeBlocks(blocks: BlockInstance[], ...): ... {
  for (const block of blocks) {
    if (block.type === 'scope' || block.type === 'xy_graph' || block.type === 'scope_3d') {
      result.push({ block, flattenedId, displayName })
    }
    // ...
  }
}
```

### 7.2 Route to Component in Render

```typescript
// Check if this is a 3D scope
const is3DScope = signals.length > 0 && signals[0].is3D

if (is3DScope && signals.length > 0) {
  return (
    <Scope3DWindow
      key={blockId}
      blockId={blockId}
      blockName={blockName}
      signal={signals[0]}
      windowState={windowState}
      zIndex={zIndex}
      onFocus={() => bringToFront(blockId)}
    />
  )
}
```

### 7.3 Set Default Window Size (Optional)

In the auto-open logic:

```typescript
const is3DScope = scope.signals[0]?.is3D
const windowSize = is3DScope ? { width: 500, height: 450 } : undefined
openPlotWindow(scope.blockId, { x: ..., y: ... }, windowSize)
```

---

## Step 8: Code Generation (Optional)

If you want the block to work in compiled simulations, add templates for each language.

### Location

- C: `backend/src/codegen/languages/c/blocks/sinks.py`
- C++: `backend/src/codegen/languages/cpp/blocks/sinks.py`
- Python: `backend/src/codegen/languages/python/blocks/sinks.py`
- Rust: `backend/src/codegen/languages/rust/blocks/sinks.py`

### Example Pattern

```python
def generate_scope_3d(block: CompiledBlock, ctx: CodeGenContext) -> str:
    # Generate state variables for recording
    # Generate update code to store values
    # Generate output code to write CSV
```

---

## Step 9: Create an Example Model

Create a JSON example in `examples/`:

```json
{
  "id": "example-id",
  "metadata": {
    "name": "Example Name",
    "description": "Description of the example"
  },
  "blocks": [
    // ... block definitions with your new plot type
  ],
  "connections": [...],
  "simulationConfig": {
    "solver": "rk4",
    "stopTime": 50,
    "stepSize": 0.01
  }
}
```

### Register in Backend

Add to `EXAMPLE_MANIFEST` in `backend/src/api/routes/examples.py`:

```python
{
    "id": "50_lorenz_attractor_3d",
    "name": "Lorenz Attractor (3D)",
    "description": "Classic chaotic attractor visualized with 3D Scope",
    "category": "advanced",
},
```

---

## Step 10: Add Unit Tests

Create tests in `backend/tests/test_<block_name>.py`:

```python
class TestScope3DBlock:
    def test_initialization_default(self):
        scope = Scope3D()
        assert scope.x_label == "X"
        # ...

    def test_rpt_records_when_ready(self):
        scope = Scope3D()
        State.ready = 1
        State.t = 1.0
        scope.inputs = [1.0, 2.0, 3.0]
        scope.rpt()
        assert len(scope.times) == 1
        # ...

    def test_get_data(self):
        scope = Scope3D()
        # ... populate data
        data = scope.getData()
        assert "x" in data
        assert "y" in data
        assert "z" in data
        assert "is3D" not in data  # Added by adapter
```

---

## Summary Checklist

- [ ] Create OSK block class with `init()`, `update()`, `rpt()`, `getData()`
- [ ] Export from `backend/src/osk/blocks/__init__.py`
- [ ] Add to `BLOCK_MAP` in `osk_adapter.py`
- [ ] Add to `PARAM_MAP` in `osk_adapter.py`
- [ ] Add to sink blocks tracking
- [ ] Handle data collection (skip in `_record_outputs`, add to `get_scope_data`)
- [ ] Handle named port connections if applicable
- [ ] Call `get_scope_data()` from `SimulationRunner.get_results()`
- [ ] Add block definition in `frontend/src/blocks/`
- [ ] Extend `SignalData` type
- [ ] Create plot component
- [ ] Add routing in `PlotWindowManager`
- [ ] (Optional) Add code generation templates
- [ ] Create example model
- [ ] Register example in backend manifest
- [ ] Add unit tests

---

## Data Flow Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  OSK Block      │     │  OSKAdapter      │     │  SimRunner      │
│  (Scope3D)      │     │                  │     │                 │
├─────────────────┤     ├──────────────────┤     ├─────────────────┤
│ rpt() records   │────>│ get_scope_data() │────>│ get_results()   │
│ x,y,z values    │     │ calls getData()  │     │ returns signals │
│                 │     │ adds is3D flag   │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          v
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Plot Component │<────│  PlotWindowMgr   │<────│  Frontend API   │
│  (Scope3DWindow)│     │  routes by is3D  │     │  fetches results│
└─────────────────┘     └──────────────────┘     └─────────────────┘
```
