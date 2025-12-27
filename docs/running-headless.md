# Running LibreSim Without the Frontend

LibreSim can be run in headless mode (without the web frontend) for scripting, batch processing, testing, or integration with other tools. This document describes the approaches available.

## Option 1: Direct Python API

The OSK (Object-oriented Simulation Kernel) can be used directly in Python scripts without any web infrastructure.

### Basic Example

```python
from src.osk.sim import Simulation
from src.osk.blocks.sources import Constant, SineWave
from src.osk.blocks.math_ops import Sum, Gain
from src.osk.blocks.continuous import Integrator
from src.osk.blocks.sinks import Scope

# Create blocks
sine = SineWave(amplitude=1.0, frequency=1.0)
gain = Gain(gain=2.0)
integrator = Integrator(initial_condition=0.0)
scope = Scope(num_inputs=2)

# Connect blocks
gain.connectInput(sine)
integrator.connectInput(gain)
scope.connectInput(sine, port=0)
scope.connectInput(integrator, port=1)

# Create simulation
sim = Simulation(dt=0.001)
sim.addBlock(sine)
sim.addBlock(gain)
sim.addBlock(integrator)
sim.addBlock(scope)

# Run simulation
sim.init()
for _ in range(10000):  # 10 seconds at dt=0.001
    sim.step()

# Access results
data = scope.getData()
times = data['times']
signals = data['signals']
```

### Working with State

The simulation state can be controlled via the `State` class:

```python
from src.osk.state import State

# Configure time step
State.dt = 0.001
State.time = 0.0

# Check if ready for output recording
if State.ready:
    # Record outputs
    pass
```

## Option 2: Backend REST API

Start only the backend server and interact via HTTP requests.

### Starting the Backend

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 9000
```

Or using the conda environment:

```bash
/c/Users/Mason/anaconda3/envs/libresim/python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 9000
```

### API Endpoints

#### Run Simulation

```bash
curl -X POST http://localhost:9000/api/simulate/run \
  -H "Content-Type: application/json" \
  -d @model.json
```

Where `model.json` contains the model definition:

```json
{
  "model": {
    "id": "test-model",
    "blocks": [...],
    "connections": [...]
  },
  "config": {
    "solver": "rk4",
    "startTime": 0,
    "stopTime": 10,
    "stepSize": 0.001
  }
}
```

#### Get Results

```bash
curl http://localhost:9000/api/simulate/results/{run_id}
```

## Option 3: Running via Docker (Backend Only)

Modify `docker-compose.yml` to run only the backend:

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "9000:9000"
    volumes:
      - ./backend:/app
    environment:
      - ENVIRONMENT=development
    command: uvicorn src.main:app --host 0.0.0.0 --port 9000
```

Then:

```bash
docker-compose up backend
```

## Option 4: Using the OSKAdapter Programmatically

For more control, use the `OSKAdapter` which handles model compilation:

```python
from src.simulation.osk_adapter import OSKAdapter
from src.models.model import Model
from src.models.simulation import SimulationConfig

# Create model from JSON
model_data = {
    "id": "test",
    "blocks": [
        {"id": "sine1", "type": "sine_wave", "parameters": {"amplitude": 1}},
        {"id": "scope1", "type": "scope", "parameters": {"numInputs": 1}}
    ],
    "connections": [
        {"sourceBlockId": "sine1", "targetBlockId": "scope1", "targetPort": 0}
    ]
}

model = Model(**model_data)
config = SimulationConfig(solver="rk4", startTime=0, stopTime=10, stepSize=0.001)

# Create adapter and run
adapter = OSKAdapter(model, config)
results = adapter.run()

# Access signal data
for signal in results['signals']:
    print(f"{signal['name']}: {len(signal['values'])} samples")
```

## Option 5: pytest for Testing

Run the test suite which exercises all blocks:

```bash
cd backend
python -m pytest -v
```

Run specific block tests:

```bash
python -m pytest tests/test_blocks.py::TestIntegrator -v
```

## Batch Processing Example

Process multiple model files:

```python
import json
from pathlib import Path
from src.simulation.osk_adapter import OSKAdapter
from src.models.model import Model
from src.models.simulation import SimulationConfig

def run_model_file(model_path: Path, config: SimulationConfig):
    with open(model_path) as f:
        model_data = json.load(f)

    model = Model(**model_data)
    adapter = OSKAdapter(model, config)
    return adapter.run()

# Process all examples
config = SimulationConfig(solver="rk4", startTime=0, stopTime=10, stepSize=0.001)
for model_file in Path("examples").glob("*.json"):
    print(f"Running {model_file.name}...")
    results = run_model_file(model_file, config)
    print(f"  {len(results.get('signals', []))} signals recorded")
```

## Key Classes Reference

| Class | Module | Purpose |
|-------|--------|---------|
| `Simulation` | `src.osk.sim` | Main simulation orchestrator |
| `State` | `src.osk.state` | Global simulation state (time, dt) |
| `Block` | `src.osk.block` | Base class for all blocks |
| `OSKAdapter` | `src.simulation.osk_adapter` | Converts model JSON to OSK blocks |
| `SimulationRunner` | `src.simulation.runner` | High-level runner with async support |

## Environment Setup

Ensure you're in the correct conda environment:

```bash
conda activate libresim
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

Or on Windows:

```powershell
conda activate libresim
cd backend
$env:PYTHONPATH = "$env:PYTHONPATH;$(Get-Location)"
```
