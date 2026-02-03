# LibreSim Blockset Development Guide

This document describes all steps required to add a new blockset (toolbox) to LibreSim, from backend implementation to frontend integration.

## Overview

Adding a new blockset requires changes in multiple locations:

1. **Backend**: Python block implementations
2. **Backend**: Unit tests for blocks
3. **Backend**: Block registration (adapter + `__init__.py`)
4. **Frontend**: TypeScript block definitions
5. **Frontend**: Category labels and colors (Sidebar)
6. **Frontend**: Type definitions (BlockCategory)
7. **Examples**: Representative JSON models

---

## Step 1: Backend Block Implementation

### Location
`backend/src/osk/blocks/<toolbox_name>.py`

### Template

```python
"""<Toolbox Name> Toolbox blocks for LibreSim."""

from typing import Optional
from ..block import Block
from ..state import State

# Optional: Define constants used by blocks
SOME_CONSTANT = 1.234

class MyBlock(Block):
    """Description of what this block does.

    Inputs:
        in1: Description of input 1

    Outputs:
        out: Description of output

    Parameters:
        param1: Description of parameter
    """

    def __init__(self, param1: float = 1.0, param2: Optional[list] = None):
        super().__init__()
        self.param1 = param1
        self.param2 = param2 if param2 is not None else [0.0]

        # Internal state
        self._internal_state = 0.0

    def init(self):
        """Called once at simulation start. Reset internal state here."""
        self._internal_state = 0.0

    def update(self):
        """Called every simulation step. Compute outputs from inputs."""
        # Get input (scalar or vector)
        input_val = self.getInput()  # or self.getInputVector() for vectors

        # Apply computation
        result = input_val * self.param1

        # Update internal state if needed
        self._internal_state = result

        # Set output
        self.output = result
        # For vector outputs: self.output = [result1, result2, result3]

    def getOutput(self, port: int = 0) -> float:
        """Return scalar output."""
        return self.output

    def getOutputVector(self) -> list:
        """Return vector output."""
        return self.output if isinstance(self.output, list) else [self.output]
```

### Key Block Base Class Methods

| Method | Description |
|--------|-------------|
| `self.getInput(port=0)` | Get scalar input from port |
| `self.getInputVector(port=0)` | Get vector input from port |
| `self.setInput(value, port=0)` | Set input (used by test harness) |
| `self.getOutput(port=0)` | Return scalar output |
| `self.getOutputVector()` | Return vector output |
| `State.t` | Current simulation time |
| `State.dt` | Simulation timestep |

---

## Step 2: Backend Unit Tests

### Location
`backend/tests/test_<toolbox_name>.py`

### Template

```python
"""Unit tests for <Toolbox Name> blocks."""

import math
import pytest

from src.osk.blocks.<toolbox_name> import (
    MyBlock,
    AnotherBlock,
)


class TestMyBlock:
    """Tests for MyBlock."""

    def test_basic_operation(self):
        """Test the primary function of the block."""
        block = MyBlock(param1=2.0)

        block.setInput(5.0)
        block.update()

        assert abs(block.getOutput() - 10.0) < 1e-6

    def test_edge_case(self):
        """Test edge cases and boundary conditions."""
        block = MyBlock(param1=0.0)

        block.setInput(100.0)
        block.update()

        assert block.getOutput() == 0.0

    def test_vector_operation(self):
        """Test with vector inputs if applicable."""
        block = MyBlock()

        block.setInput([1.0, 2.0, 3.0])
        block.update()

        output = block.getOutputVector()
        assert len(output) == 3
```

### Running Tests

```bash
cd backend
python -m pytest tests/test_<toolbox_name>.py -v
```

---

## Step 3: Backend Block Registration

### 3a. Update `__init__.py`

**File**: `backend/src/osk/blocks/__init__.py`

Add imports at the top:

```python
from .<toolbox_name> import (
    MyBlock,
    AnotherBlock,
)
```

Add to `__all__` list:

```python
__all__ = [
    # ... existing entries ...
    # <Toolbox Name>
    "MyBlock", "AnotherBlock",
]
```

### 3b. Update OSK Adapter

**File**: `backend/src/simulation/osk_adapter.py`

Add imports:

```python
from src.osk.blocks.<toolbox_name> import (
    MyBlock,
    AnotherBlock,
)
```

Add to `BLOCK_TYPE_MAP`:

```python
BLOCK_TYPE_MAP: Dict[str, Type[Block]] = {
    # ... existing entries ...
    # <Toolbox Name>
    "my_block": MyBlock,
    "another_block": AnotherBlock,
}
```

Add parameter mappings to `PARAM_MAP` (frontend name -> backend name):

```python
PARAM_MAP: Dict[str, Dict[str, str]] = {
    # ... existing entries ...
    "my_block": {
        "param1": "param1",
        "myParameter": "my_parameter",  # camelCase -> snake_case
    },
}
```

---

## Step 4: Frontend Block Definitions

### Location
`frontend/src/blocks/<toolbox_name>.ts`

### Template

```typescript
import type { BlockDefinition } from '../types/block'

export const <toolboxName>Blocks: BlockDefinition[] = [
  {
    type: 'my_block',  // Must match BLOCK_TYPE_MAP key
    category: '<toolbox_name>',  // Must match BlockCategory
    name: 'My Block',
    description: 'Description shown in tooltip',
    inputs: [
      { name: 'in', dataType: 'double', dimensions: [1] },
    ],
    outputs: [
      { name: 'out', dataType: 'double', dimensions: [1] },
    ],
    parameters: [
      {
        name: 'param1',  // Must match PARAM_MAP key
        type: 'number',
        default: 1.0,
        label: 'Parameter 1',
        description: 'Optional description',
        min: 0,
        max: 100,
        step: 0.1,
      },
      {
        name: 'selectParam',
        type: 'select',
        default: 'option1',
        label: 'Select Parameter',
        options: [
          { value: 'option1', label: 'Option 1' },
          { value: 'option2', label: 'Option 2' },
        ],
      },
      {
        name: 'arrayParam',
        type: 'array',
        default: [1, 2, 3],
        label: 'Array Parameter',
      },
    ],
    icon: 'MB',  // Short text shown in block
  },
]
```

### Parameter Types

| Type | Description |
|------|-------------|
| `number` | Numeric input (supports min, max, step) |
| `string` | Text input |
| `boolean` | Checkbox |
| `select` | Dropdown (requires options array) |
| `array` | Array input (JSON format) |

### Dimension Conventions

- `[1]` - Scalar
- `[3]` - Fixed 3-element vector
- `[-1]` - Variable-length vector
- `[9]` - 3x3 matrix (row-major)

---

## Step 5: Frontend Index Registration

**File**: `frontend/src/blocks/index.ts`

Add import:

```typescript
import { <toolboxName>Blocks } from './<toolbox_name>'
```

Add to `builtInBlocks` array:

```typescript
const builtInBlocks: BlockDefinition[] = [
  // ... existing entries ...
  ...<toolboxName>Blocks,
]
```

Add to `blockCategories` array:

```typescript
export const blockCategories: BlockCategory[] = [
  // ... existing entries ...
  '<toolbox_name>',
]
```

Add export:

```typescript
export { <toolboxName>Blocks } from './<toolbox_name>'
```

---

## Step 6: Frontend Type Definition

**File**: `frontend/src/types/block.ts`

Add to `BlockCategory` union type:

```typescript
export type BlockCategory =
  | 'sources'
  // ... existing entries ...
  | '<toolbox_name>'
```

---

## Step 7: Sidebar Labels and Colors

**File**: `frontend/src/components/Sidebar/Sidebar.tsx`

Add category label:

```typescript
const categoryLabels: Record<BlockCategory, string> = {
  // ... existing entries ...
  <toolbox_name>: '<Toolbox Display Name>',
}
```

Add category color:

```typescript
const categoryColors: Record<BlockCategory, string> = {
  // ... existing entries ...
  <toolbox_name>: 'bg-<color>-600',  // Tailwind color class
}
```

### Available Colors

Choose from Tailwind palette: `red`, `orange`, `amber`, `yellow`, `lime`, `green`, `emerald`, `teal`, `cyan`, `sky`, `blue`, `indigo`, `violet`, `purple`, `fuchsia`, `pink`, `rose`

---

## Step 8: Example Models

### Location
`examples/<number>_<descriptive_name>.json`

### Template

```json
{
  "id": "example-<name>",
  "metadata": {
    "name": "Example Display Name",
    "description": "What this example demonstrates...",
    "author": "LibreSim Examples",
    "createdAt": "2024-12-31T00:00:00Z",
    "modifiedAt": "2024-12-31T00:00:00Z",
    "version": "1.0.0"
  },
  "blocks": [
    {
      "id": "block1",
      "type": "my_block",
      "name": "Block Display Name",
      "position": { "x": 100, "y": 100 },
      "parameters": { "param1": 2.0 },
      "inputPorts": [
        { "id": "block1-in", "name": "in", "dataType": "double", "dimensions": [1] }
      ],
      "outputPorts": [
        { "id": "block1-out", "name": "out", "dataType": "double", "dimensions": [1] }
      ]
    }
  ],
  "connections": [
    {
      "id": "c1",
      "sourceBlockId": "source_block",
      "sourcePortId": "source_block-out",
      "targetBlockId": "block1",
      "targetPortId": "block1-in"
    }
  ],
  "simulationConfig": {
    "solver": "rk4",
    "startTime": 0,
    "stopTime": 10,
    "stepSize": 0.01
  }
}
```

---

## Step 9: Register Examples in Examples Modal

For examples to appear in the Examples Modal, you must register them in the frontend.

### 9a. Update ExampleInfo Type

**File**: `frontend/src/data/examples.ts`

Add the new category to the `ExampleInfo` type:

```typescript
export interface ExampleInfo {
  id: string
  name: string
  description: string
  category: 'basic' | 'control' | ... | '<toolbox_name>'
}
```

### 9b. Add Example List Entries

**File**: `frontend/src/data/examples.ts`

Add entries to the `exampleList` array:

```typescript
export const exampleList: ExampleInfo[] = [
  // ... existing entries ...
  // <Toolbox Name>
  {
    id: '40_my_example',  // Must match filename without .json
    name: 'My Example Name',
    description: 'Short description of what this example shows',
    category: '<toolbox_name>',
  },
]
```

### 9c. Add Embedded Example Data

**File**: `frontend/src/data/examples.ts`

Add the full model data to `embeddedExamples` object (copy JSON content):

```typescript
export const embeddedExamples: Record<string, Model> = {
  // ... existing entries ...
  '40_my_example': {
    id: 'example-my-example',
    metadata: { ... },
    blocks: [ ... ],
    connections: [ ... ],
    simulationConfig: { ... },
  },
}
```

### 9d. Update ExamplesModal Category Info

**File**: `frontend/src/components/Examples/ExamplesModal.tsx`

Update the `ExampleInfo` type (must match examples.ts):

```typescript
export interface ExampleInfo {
  id: string
  name: string
  description: string
  category: 'basic' | 'control' | ... | '<toolbox_name>'
}
```

Add category info entry:

```typescript
const categoryInfo: Record<string, { title: string; description: string; icon: string }> = {
  // ... existing entries ...
  <toolbox_name>: {
    title: '<Toolbox Display Name>',
    description: 'Brief description of toolbox examples',
    icon: '🔧',  // Choose an appropriate emoji
  },
}
```

Add to category order:

```typescript
const categoryOrder = ['basic', 'control', ..., '<toolbox_name>', 'advanced']
```

**Note**: Keep 'advanced' at the end of the order for consistency.

---

## Checklist

Use this checklist when adding a new blockset:

- [ ] Create `backend/src/osk/blocks/<toolbox>.py` with block classes
- [ ] Create `backend/tests/test_<toolbox>.py` with unit tests
- [ ] Run tests: `python -m pytest tests/test_<toolbox>.py -v`
- [ ] Update `backend/src/osk/blocks/__init__.py` (imports + __all__)
- [ ] Update `backend/src/simulation/osk_adapter.py` (BLOCK_TYPE_MAP + PARAM_MAP)
- [ ] Create `frontend/src/blocks/<toolbox>.ts` with definitions
- [ ] Update `frontend/src/blocks/index.ts` (import, builtInBlocks, categories, export)
- [ ] Update `frontend/src/types/block.ts` (BlockCategory type)
- [ ] Update `frontend/src/components/Sidebar/Sidebar.tsx` (labels + colors)
- [ ] Create example models in `examples/` directory
- [ ] Update `frontend/src/data/examples.ts` (ExampleInfo type, exampleList, embeddedExamples)
- [ ] Update `frontend/src/components/Examples/ExamplesModal.tsx` (ExampleInfo type, categoryInfo, categoryOrder)
- [ ] Test in browser to verify blocks appear and simulate correctly
- [ ] Test Examples Modal to verify examples load correctly

---

## Common Issues

### Examples don't appear in Examples Modal
- Verify category is added to `ExampleInfo` type in both `examples.ts` and `ExamplesModal.tsx`
- Check that `categoryInfo` has an entry with title, description, and icon
- Ensure category is added to `categoryOrder` array
- Verify example entries are in `exampleList` with correct `id` matching embedded data key
- Confirm full model data is added to `embeddedExamples` object

### Block doesn't appear in sidebar
- Check that category is added to `blockCategories` array
- Verify `BlockCategory` type includes the new category
- Ensure `categoryLabels` and `categoryColors` have entries

### Block simulation fails
- Verify `BLOCK_TYPE_MAP` has correct mapping
- Check `PARAM_MAP` for parameter name mismatches
- Ensure all required parameters have defaults

### Port connection errors
- Verify input/output port definitions match block class
- Check dimension arrays match expected data shapes
