# LibreSim

A web-based block diagram simulation tool inspired by Simulink, powered by the Object-oriented Simulation Kernel (OSK).

## Overview

LibreSim provides a graphical environment for modeling, simulating, and analyzing dynamic systems. It features a drag-and-drop block diagram editor, real-time simulation visualization, and support for importing Simulink `.mdl` files.

## Features

- **Visual Block Diagram Editor**: Drag-and-drop interface for building system models
- **Control Systems Focus**: Comprehensive library of blocks for control system design
- **Real-time Simulation**: Live visualization of simulation results with scopes and plots
- **Simulink Import**: Import existing `.mdl` model files
- **Multiple Solvers**: RK4, Euler, and Merson's method ODE solvers
- **Extensible Architecture**: Easy to add custom blocks and solvers

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (React)                        │
│  Block Editor │ Properties Panel │ Simulation Viewer    │
└─────────────────────────┬───────────────────────────────┘
                          │ REST API / WebSocket
┌─────────────────────────▼───────────────────────────────┐
│                  Backend (FastAPI)                       │
│  Model Management │ Simulation Control │ MDL Parser     │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│           Object-oriented Simulation Kernel (OSK)        │
│  Blocks │ Signals │ Solvers │ Simulation Engine         │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker (optional, for containerized deployment)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/LibreSim.git
   cd LibreSim
   ```

2. **Start the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn src.main:app --reload --port 9000
   ```

3. **Start the frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Open in browser**
   Navigate to `http://localhost:4200`

### Using Docker

```bash
docker-compose up --build
```

## Project Structure

```
LibreSim/
├── frontend/           # React application
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── blocks/     # Block type definitions
│   │   ├── store/      # State management
│   │   └── api/        # API client
│   └── package.json
├── backend/            # FastAPI server
│   ├── src/
│   │   ├── api/        # REST endpoints
│   │   ├── simulation/ # OSK integration
│   │   ├── blocks/     # Block implementations
│   │   └── parsers/    # MDL file parser
│   └── requirements.txt
├── osk/                # Object-oriented Simulation Kernel
└── docs/               # Documentation
```

## Block Library

### Sources
- Constant, Step, Ramp, Sine Wave, Pulse Generator, Clock

### Sinks
- Scope, Display, To Workspace, XY Graph

### Continuous
- Integrator, Derivative, Transfer Function, State-Space, PID Controller

### Math Operations
- Sum, Gain, Product, Abs, Sign, Math Function

### Discrete
- Unit Delay, Zero-Order Hold, Discrete Transfer Function

### Signal Routing
- Mux, Demux, Switch, Multiport Switch

## Simulink Import

LibreSim supports importing Simulink `.mdl` files:

```python
# Via API
POST /api/models/import
Content-Type: multipart/form-data
file: your_model.mdl
```

Or drag-and-drop an `.mdl` file directly into the editor.

## Configuration

### Simulation Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `solver` | `rk4` | ODE solver (euler, rk4, merson) |
| `startTime` | `0.0` | Simulation start time |
| `stopTime` | `10.0` | Simulation stop time |
| `stepSize` | `0.01` | Fixed step size |
| `maxStep` | `auto` | Maximum step size (variable step) |

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Object-oriented Simulation Kernel (OSK) by Mason Nixon
- Inspired by MathWorks Simulink
