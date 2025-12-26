# Control Analysis Visualization Design

## Overview

This document describes the planned redesign of control analysis blocks (BodePlot, NyquistPlot, PoleZeroMap, StepInfo) to provide proper visualization capabilities.

## Goals

1. **Accept Transfer Function input** from connected blocks (instead of embedding TF parameters)
2. **Return visualization-specific data structures** to the frontend
3. **Render custom visualizations** for each analysis type with proper annotations

## Current Implementation

### Backend (control_analysis.py)
- Blocks compute analysis in `init()` using embedded numerator/denominator parameters
- Have `connectInput(block, port)` and `setInput(value, port)` methods but don't use them
- Have `get_*_data()` methods returning comprehensive analysis data

### Frontend (PlotWindow.tsx)
- Uses Plotly.js for rendering via `react-plotly.js`
- SignalData structure supports both `values: number[]` and `values: number[][]`
- PlotWindowManager opens windows for `scope` and `xy_graph` block types

---

## Proposed Changes

### Phase 1: Backend - Modify Control Analysis Blocks

**File: `backend/src/osk/blocks/control_analysis.py`**

1. Modify all four blocks to accept TF input from connected block:

```python
def init(self):
    # If connected to a TransferFunction block, extract its coefficients
    if self.input_block and hasattr(self.input_block, 'numerator'):
        self.numerator = list(self.input_block.numerator)
        self.denominator = list(self.input_block.denominator)
    # Compute analysis with these coefficients
    self._compute_...()
```

2. Add `getData()` method to each block (similar to Scope):

```python
def getData(self):
    """Return analysis data for visualization."""
    return {
        'analysisType': 'bode',  # or 'nyquist', 'pzmap', 'stepinfo'
        **self.get_bode_data()   # Merge existing analysis data
    }
```

3. Register blocks as sink blocks so their data is collected

### Phase 2: Backend - Extend Result Collection

**File: `backend/src/simulation/osk_adapter.py`**

- Add control analysis block types to `_sink_blocks` list during `_create_osk_block()`
- Handle analysis blocks specially - call `getData()` once at end

**File: `backend/src/simulation/runner.py`**

Return structure:
```python
{
    "signals": [...],  # Regular time-series
    "analyses": {      # Analysis block data
        "blockId": { "analysisType": "bode", "frequencies": [...], ... }
    },
    "statistics": {...}
}
```

### Phase 3: Frontend - Extend Types

**File: `frontend/src/types/simulation.ts`**

```typescript
interface AnalysisData {
  blockId: string
  analysisType: 'bode' | 'nyquist' | 'pzmap' | 'stepinfo'
  // Bode-specific
  frequencies?: number[]
  magnitude_db?: number[]
  phase_deg?: number[]
  gain_margin?: number | null
  phase_margin?: number | null
  // Nyquist-specific
  real?: number[]
  imag?: number[]
  encirclements?: number
  // Pole-Zero specific
  poles?: [number, number][]
  zeros?: [number, number][]
  is_stable?: boolean
  // Step response specific
  times?: number[]
  response?: number[]
  rise_time?: number | null
  settling_time?: number | null
  overshoot_percent?: number | null
  peak_time?: number | null
  peak_value?: number | null
  steady_state_value?: number | null
}

interface SimulationResults {
  signals: SignalData[]
  analyses?: Record<string, AnalysisData>
  statistics: SimulationStatistics
}
```

### Phase 4: Frontend - Create Visualization Components

**New Files in `frontend/src/components/Analysis/`:**

#### BodePlotWindow.tsx
- Dual subplot layout (magnitude on top, phase on bottom)
- X-axis: log frequency scale (rad/s or Hz)
- Top Y-axis: Magnitude (dB)
- Bottom Y-axis: Phase (degrees)
- Markers for gain/phase crossover frequencies
- Display gain margin and phase margin values

#### NyquistPlotWindow.tsx
- Single plot: Real vs Imaginary axes
- Curve showing H(jw) as w varies
- Mark the -1+0j point (critical point)
- Show encirclement count
- Arrow indicators showing direction of increasing frequency

#### PoleZeroMapWindow.tsx
- Complex plane visualization
- X markers for poles
- O markers for zeros
- Grid lines at real and imaginary axes
- Color coding: stable poles (green), unstable poles (red)
- Show dominant pole highlighted

#### StepResponseWindow.tsx
- Time-domain plot with response curve
- Annotated metrics on the plot:
  - Rise time (10% to 90% lines)
  - Settling time (2% band shown)
  - Peak overshoot (horizontal line at peak, percentage label)
  - Steady-state value (horizontal line)
- Metric values displayed in legend or info panel

---

## Visualization Mockups

### Bode Plot
```
+------------------------------------------+
|  Magnitude (dB)                          |
|  20 |----*                               |
|   0 |      \______                       |
| -20 |             \____                  |
| -40 |                  \____             |
|  -+-----------+------------+----------+  |
|  0.01        0.1         1          10   |
+------------------------------------------+
|  Phase (degrees)                         |
|   0 |----*                               |
| -90 |      \______                       |
|-180 |             \____*___              |
|-270 |                      \____         |
|  -+-----------+------------+----------+  |
|  0.01        0.1         1          10   |
|              Frequency (rad/s)           |
+------------------------------------------+
| Gain Margin: XX dB @ Y rad/s             |
| Phase Margin: XX deg @ Y rad/s           |
+------------------------------------------+
```

### Nyquist Plot
```
+------------------------------------------+
|              Im                          |
|              |                           |
|           2  +                           |
|              |    ___                    |
|           1  +   /   \                   |
|              |  |     |                  |
| --+--+--+--+-+-+--+--+--+-- Re          |
| -3  -2  -1 (X) 1  |  2  3               |
|              |  \     /                  |
|          -1  +   \___/                   |
|              |                           |
|          -2  +                           |
+------------------------------------------+
| (X) = Critical point (-1, 0)             |
| Encirclements: 0 (Stable)                |
+------------------------------------------+
```

### Pole-Zero Map
```
+------------------------------------------+
|              Im                          |
|              |                           |
|           2  +    X (pole)               |
|              |                           |
|           1  +                           |
|              |                           |
| --+--+--+--+-+-+--+--+--+-- Re          |
| -3  -2  -1   0   1  2  3                |
|              |                           |
|          -1  +                           |
|              |                           |
|          -2  +    X (pole)               |
|              | O (zero)                  |
+------------------------------------------+
| Poles: -1+2j, -1-2j                      |
| Zeros: none                              |
| Stable: Yes (all poles in LHP)           |
+------------------------------------------+
```

### Step Response
```
+------------------------------------------+
|  1.3 +         * Peak (Mp)               |
|      |        /|\                        |
|  1.0 +-------/-+-\------- Steady State   |
|      |      /  |  \                      |
|  0.9 +-----/---+---\----- 90% line       |
|      |    /    |    \____                |
|  0.1 +---/-----+-----------              |
|      |  /      |                         |
|    0 +---------+---------+--------+      |
|      0    Tr  Tp   Ts            10      |
|              Time (s)                    |
+------------------------------------------+
| Rise Time (Tr): X.XX s                   |
| Peak Time (Tp): X.XX s                   |
| Settling Time (Ts): X.XX s               |
| Overshoot (Mp): XX.X%                    |
| Steady-State: X.XX                       |
+------------------------------------------+
```

---

## Files to Modify

### Backend
- `backend/src/osk/blocks/control_analysis.py` - Accept TF input, add getData()
- `backend/src/simulation/osk_adapter.py` - Register analysis blocks as sinks
- `backend/src/simulation/runner.py` - Include analysis data in results

### Frontend
- `frontend/src/types/simulation.ts` - Add AnalysisData interface
- `frontend/src/components/Analysis/BodePlotWindow.tsx` - NEW
- `frontend/src/components/Analysis/NyquistPlotWindow.tsx` - NEW
- `frontend/src/components/Analysis/PoleZeroMapWindow.tsx` - NEW
- `frontend/src/components/Analysis/StepResponseWindow.tsx` - NEW
- `frontend/src/components/Simulation/PlotWindowManager.tsx` - Handle analysis blocks
- `frontend/src/blocks/control_analysis.ts` - Update block definitions to accept input

### Examples
- `examples/07a_bode_plot_analysis.json` - Use TF block as input
- `examples/07b_nyquist_plot_analysis.json` - Use TF block as input
- `examples/07c_pole_zero_map.json` - Use TF block as input
- `examples/07d_step_response_info.json` - Use TF block as input
- `frontend/src/data/examples.ts` - Update embedded examples

---

## Implementation Order

1. Backend: Modify control_analysis.py blocks to accept TF input
2. Backend: Add getData() methods and register as sinks
3. Backend: Extend runner.py to include analysis data
4. Frontend: Add AnalysisData types
5. Frontend: Create BodePlotWindow component
6. Frontend: Create NyquistPlotWindow component
7. Frontend: Create PoleZeroMapWindow component
8. Frontend: Create StepResponseWindow component
9. Frontend: Update PlotWindowManager to handle analysis blocks
10. Update examples to use TF block as input
11. Run tests and verify visualizations
