import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useUIStore } from '../../store/uiStore'
import { api } from '../../api/client'

// Block reference documentation
const blockReference = {
  sources: {
    title: 'Sources',
    description: 'Generate input signals for your model',
    blocks: [
      { name: 'Constant', icon: 'C', description: 'Outputs a constant value', parameters: 'value' },
      { name: 'Step', icon: '⌐', description: 'Generates a step function at specified time', parameters: 'stepTime, initialValue, finalValue' },
      { name: 'Ramp', icon: '/', description: 'Generates a linearly increasing signal', parameters: 'slope, startTime, initialOutput' },
      { name: 'Sine Wave', icon: '~', description: 'Generates a sinusoidal waveform', parameters: 'amplitude, frequency, phase, bias' },
      { name: 'Pulse Generator', icon: '⎍', description: 'Generates square wave pulses', parameters: 'amplitude, period, dutyCycle, phaseDelay' },
      { name: 'Clock', icon: '⏱', description: 'Outputs the current simulation time', parameters: 'none' },
      { name: 'White Noise', icon: '∿', description: 'Generates random noise with Gaussian distribution', parameters: 'mean, variance, seed, sampleTime' },
      { name: 'Uniform Noise', icon: '≋', description: 'Generates uniformly distributed random noise', parameters: 'minimum, maximum, seed, sampleTime' },
      { name: 'Repeating Sequence', icon: '⟳', description: 'Outputs values from a repeating time/value table', parameters: 'timeValues, outputValues' },
      { name: 'Chirp Signal', icon: '↗~', description: 'Frequency-sweeping sinusoid (chirp)', parameters: 'initialFrequency, targetTime, targetFrequency' },
      { name: 'Band-Limited White Noise', icon: '∿B', description: 'Band-limited Gaussian noise', parameters: 'noisePower, sampleTime, seed' },
      { name: 'Ground', icon: '⏚', description: 'Outputs zero (ground reference)', parameters: 'none' },
      { name: 'From Workspace', icon: '📥', description: 'Reads signal data from workspace', parameters: 'timeData, valueData, interpolation' },
      { name: 'Signal Generator', icon: 'SG', description: 'Multi-waveform signal generator', parameters: 'waveType, amplitude, frequency, units' },
    ],
  },
  sinks: {
    title: 'Sinks',
    description: 'Display and record simulation outputs',
    blocks: [
      { name: 'Scope', icon: '📊', description: 'Displays signals as time-series plots', parameters: 'numInputs' },
      { name: 'Display', icon: '7seg', description: 'Shows current signal value numerically', parameters: 'none' },
      { name: 'To Workspace', icon: '📤', description: 'Saves signal data to workspace', parameters: 'variableName' },
      { name: 'Terminator', icon: '⊗', description: 'Terminates unconnected output lines', parameters: 'none' },
    ],
  },
  continuous: {
    title: 'Continuous',
    description: 'Continuous-time dynamic system elements',
    blocks: [
      { name: 'Integrator', icon: '∫', description: 'Integrates input signal over time', parameters: 'initialCondition, externalIC, limitOutput, upperLimit, lowerLimit' },
      { name: 'Derivative', icon: 'd/dt', description: 'Differentiates input signal (filtered)', parameters: 'coefficient' },
      { name: 'Transfer Function', icon: 'H(s)', description: 'Continuous-time transfer function', parameters: 'numerator, denominator' },
      { name: 'State-Space', icon: 'SS', description: 'State-space model (A, B, C, D matrices)', parameters: 'A, B, C, D, initialCondition' },
      { name: 'Transport Delay', icon: 'Td', description: 'Delays signal by fixed time', parameters: 'delayTime, initialOutput' },
      { name: 'Second Order', icon: '2nd', description: 'Second-order system (mass-spring-damper)', parameters: 'naturalFrequency, dampingRatio, gain' },
      { name: 'Limited Integrator', icon: '∫lim', description: 'Integrator with output saturation', parameters: 'initialCondition, upperLimit, lowerLimit' },
      { name: 'Zero-Pole', icon: 'ZP', description: 'Transfer function by zeros and poles', parameters: 'zeros, poles, gain' },
    ],
  },
  discrete: {
    title: 'Discrete',
    description: 'Discrete-time system elements',
    blocks: [
      { name: 'Unit Delay', icon: 'z⁻¹', description: 'Delays signal by one sample', parameters: 'initialCondition, sampleTime' },
      { name: 'Zero-Order Hold', icon: 'ZOH', description: 'Sample and hold continuous signal', parameters: 'sampleTime' },
      { name: 'First-Order Hold', icon: 'FOH', description: 'Sample with linear interpolation', parameters: 'sampleTime' },
      { name: 'Discrete Integrator', icon: '∫d', description: 'Discrete-time integration', parameters: 'method, sampleTime, initialCondition' },
      { name: 'Discrete Derivative', icon: 'd/dt_d', description: 'Discrete-time differentiation', parameters: 'sampleTime, initialCondition' },
      { name: 'Discrete Transfer Function', icon: 'H(z)', description: 'Discrete transfer function', parameters: 'numerator, denominator, sampleTime' },
      { name: 'Discrete State-Space', icon: 'SS_d', description: 'Discrete state-space model', parameters: 'A, B, C, D, initialState, sampleTime' },
      { name: 'Memory', icon: 'M', description: 'Stores previous timestep value', parameters: 'initialCondition' },
    ],
  },
  math: {
    title: 'Math Operations',
    description: 'Mathematical operations and functions',
    blocks: [
      { name: 'Sum', icon: '∑', description: 'Adds or subtracts inputs', parameters: 'signs (e.g., "+-+")' },
      { name: 'Gain', icon: 'K', description: 'Multiplies input by constant', parameters: 'gain' },
      { name: 'Product', icon: '×', description: 'Multiplies or divides inputs', parameters: 'operations (e.g., "**/")' },
      { name: 'Divide', icon: '÷', description: 'Divides first input by second', parameters: 'none' },
      { name: 'Abs', icon: '|x|', description: 'Absolute value of input', parameters: 'none' },
      { name: 'Sign', icon: '±', description: 'Sign function (-1, 0, or 1)', parameters: 'none' },
      { name: 'Sqrt', icon: '√', description: 'Square root of input', parameters: 'none' },
      { name: 'Square', icon: 'x²', description: 'Square of input', parameters: 'none' },
      { name: 'Power', icon: 'xⁿ', description: 'Raises input to power', parameters: 'exponent' },
      { name: 'Exp', icon: 'eˣ', description: 'Exponential function', parameters: 'none' },
      { name: 'Log', icon: 'ln', description: 'Natural logarithm', parameters: 'none' },
      { name: 'Log10', icon: 'log₁₀', description: 'Base-10 logarithm', parameters: 'none' },
      { name: 'Reciprocal', icon: '1/x', description: 'Reciprocal of input', parameters: 'none' },
      { name: 'Mod', icon: 'mod', description: 'Modulo operation', parameters: 'none' },
      { name: 'Bias', icon: '+b', description: 'Adds constant bias to input', parameters: 'bias' },
      { name: 'Saturation', icon: '⊏⊐', description: 'Limits signal to range', parameters: 'upperLimit, lowerLimit' },
      { name: 'Dead Zone', icon: '⊏ ⊐', description: 'Zero output within range', parameters: 'start, end' },
      { name: 'Unary Minus', icon: '-x', description: 'Negates input signal', parameters: 'none' },
      { name: 'Math Function', icon: 'f(x)', description: 'Various math functions', parameters: 'function (exp, log, sqrt, etc.)' },
      { name: 'Trigonometry', icon: 'sin', description: 'Trigonometric functions', parameters: 'function (sin, cos, tan, asin, etc.)' },
      { name: 'Atan2', icon: 'atan2', description: 'Four-quadrant arctangent', parameters: 'none' },
      { name: 'Hypot', icon: '√(x²+y²)', description: 'Hypotenuse of two inputs', parameters: 'none' },
      { name: 'Rounding', icon: '⌊⌉', description: 'Round, floor, ceil, or fix', parameters: 'function' },
      { name: 'MinMax', icon: 'min/max', description: 'Minimum or maximum of inputs', parameters: 'function, numInputs' },
      { name: 'Dot Product', icon: 'a·b', description: 'Vector dot product', parameters: 'none' },
      { name: 'Cross Product', icon: 'a×b', description: 'Vector cross product (3D)', parameters: 'none' },
      { name: 'Magnitude-Angle', icon: 'r∠θ', description: 'Converts real/imag to magnitude/angle', parameters: 'none' },
      { name: 'Polynomial', icon: 'p(x)', description: 'Evaluates polynomial', parameters: 'coefficients' },
      { name: 'Weighted Sum', icon: 'Σwx', description: 'Weighted sum of inputs', parameters: 'weights' },
      { name: 'Slider Gain', icon: 'K↔', description: 'Adjustable gain with limits', parameters: 'gain, min, max' },
    ],
  },
  logic: {
    title: 'Logic',
    description: 'Comparison and logical operations',
    blocks: [
      { name: 'Compare To Zero', icon: '≷0', description: 'Compares input to zero', parameters: 'operator (>, <, ==, !=, >=, <=)' },
      { name: 'Compare To Constant', icon: '≷K', description: 'Compares input to constant', parameters: 'constant, operator' },
      { name: 'Relational Operator', icon: '≷', description: 'Compares two inputs', parameters: 'operator (>, <, ==, !=, >=, <=)' },
      { name: 'Logical Operator', icon: '∧∨', description: 'AND, OR, NOT, XOR, NAND, NOR', parameters: 'operator, numInputs' },
      { name: 'Bit Operator', icon: '⊕', description: 'Bitwise operations', parameters: 'operator (AND, OR, XOR, NOT, SHIFT_LEFT, SHIFT_RIGHT)' },
    ],
  },
  routing: {
    title: 'Signal Routing',
    description: 'Route and multiplex signals',
    blocks: [
      { name: 'Mux', icon: 'Mux', description: 'Combines signals into vector', parameters: 'numInputs' },
      { name: 'Demux', icon: 'Demux', description: 'Splits vector into signals', parameters: 'numOutputs' },
      { name: 'Switch', icon: '⤨', description: 'Selects between two inputs', parameters: 'threshold, criteria' },
      { name: 'Reshape', icon: '[ ]', description: 'Reshapes signal dimensions', parameters: 'outputDimensions' },
    ],
  },
  signalProcessing: {
    title: 'Signal Processing',
    description: 'Filters and signal conditioning',
    blocks: [
      { name: 'Low-Pass Filter', icon: 'LPF', description: 'First-order low-pass filter', parameters: 'cutoffFrequency' },
      { name: 'High-Pass Filter', icon: 'HPF', description: 'First-order high-pass filter', parameters: 'cutoffFrequency' },
      { name: 'Band-Pass Filter', icon: 'BPF', description: 'Band-pass filter', parameters: 'lowCutoff, highCutoff' },
      { name: 'Notch Filter', icon: 'Notch', description: 'Band-stop (notch) filter', parameters: 'notchFrequency, bandwidth, depth' },
      { name: 'Analog Filter', icon: 'AF', description: 'Configurable analog filter', parameters: 'design, response, order, cutoffFrequency' },
      { name: 'Rate Limiter', icon: '↕', description: 'Limits rate of signal change', parameters: 'risingLimit, fallingLimit' },
      { name: 'Moving Average', icon: 'MA', description: 'Sliding window average', parameters: 'windowSize' },
      { name: 'Backlash', icon: '⊏⊐', description: 'Deadband with hysteresis', parameters: 'deadbandWidth, initialOutput' },
    ],
  },
  nonlinear: {
    title: 'Nonlinear',
    description: 'Nonlinear system elements',
    blocks: [
      { name: '1-D Lookup Table', icon: 'f(x)', description: 'Interpolates from 1D table', parameters: 'xData, yData' },
      { name: '2-D Lookup Table', icon: 'f(x,y)', description: 'Interpolates from 2D table', parameters: 'xData, yData, zData' },
      { name: 'Quantizer', icon: '|||', description: 'Rounds to discrete levels', parameters: 'interval' },
      { name: 'Relay', icon: '~|', description: 'On/off switch with hysteresis', parameters: 'switchOn, switchOff, outputOn, outputOff' },
      { name: 'Coulomb Friction', icon: 'Fr', description: 'Static and dynamic friction', parameters: 'staticGain, dynamicGain, velocityThreshold' },
      { name: 'Variable Transport Delay', icon: 'Td', description: 'Variable time delay', parameters: 'maxDelay, initialDelay' },
      { name: 'Wrap To Range', icon: '⟳', description: 'Wraps value to range (e.g., angle normalization)', parameters: 'lower, upper' },
      { name: 'Hit Crossing', icon: '⨉', description: 'Detects threshold crossings', parameters: 'threshold, direction (rising/falling/either)' },
      { name: 'Hysteresis', icon: 'H', description: 'Hysteresis switch between two outputs', parameters: 'upperThreshold, lowerThreshold, outputHigh, outputLow' },
      { name: 'Stiction', icon: 'St', description: 'Static friction model', parameters: 'breakawayForce, velocityThreshold' },
      { name: 'Slew Rate Limiter', icon: 'SR', description: 'Limits rate of change', parameters: 'risingRate, fallingRate, sampleTime' },
    ],
  },
  observers: {
    title: 'Observers',
    description: 'State estimation and filtering',
    blocks: [
      { name: 'Luenberger Observer', icon: 'L', description: 'Full-state observer', parameters: 'A, B, C, L, initialState' },
      { name: 'Kalman Filter', icon: 'KF', description: 'Optimal state estimator', parameters: 'A, B, C, Q, R, initialState, initialP' },
      { name: 'Extended Kalman Filter', icon: 'EKF', description: 'Nonlinear state estimator', parameters: 'nStates, Q, R, initialState' },
    ],
  },
  controlAnalysis: {
    title: 'Control Analysis',
    description: 'Analysis and visualization tools',
    blocks: [
      { name: 'Bode Plot', icon: 'Bode', description: 'Frequency response plot', parameters: 'numerator, denominator, minFrequency, maxFrequency' },
      { name: 'Nyquist Plot', icon: 'Nyq', description: 'Nyquist stability plot', parameters: 'numerator, denominator, minFrequency, maxFrequency' },
      { name: 'Pole-Zero Map', icon: 'PZ', description: 'Pole-zero locations', parameters: 'numerator, denominator' },
      { name: 'Step Info', icon: 'Step', description: 'Step response characteristics', parameters: 'numerator, denominator, simulationTime' },
    ],
  },
  subsystems: {
    title: 'Subsystems',
    description: 'Hierarchical model organization',
    blocks: [
      { name: 'Subsystem', icon: '[ ]', description: 'Contains a sub-model', parameters: 'numInputs, numOutputs' },
      { name: 'Inport', icon: '→', description: 'Input port for subsystem', parameters: 'portNumber' },
      { name: 'Outport', icon: '→', description: 'Output port for subsystem', parameters: 'portNumber' },
    ],
  },
  dataTypes: {
    title: 'Data Type Conversion',
    description: 'Convert signals between data types',
    blocks: [
      { name: 'Data Type Conversion', icon: 'Convert', description: 'Convert signal to different data type', parameters: 'outputType, saturationMode, roundingMode' },
      { name: 'Real-Imag to Complex', icon: 'Re+jIm', description: 'Create complex from real/imag (outputs magnitude/phase)', parameters: 'none' },
      { name: 'Complex to Real-Imag', icon: 'Re,Im', description: 'Extract real/imag from magnitude/phase', parameters: 'none' },
    ],
  },
  matrixOps: {
    title: 'Matrix Operations',
    description: 'Matrix and vector operations',
    blocks: [
      { name: 'Matrix Multiply', icon: 'A*B', description: 'Multiply matrices or vectors', parameters: 'none' },
      { name: 'Matrix Transpose', icon: "A'", description: 'Transpose a matrix or vector', parameters: 'none' },
      { name: 'Matrix Inverse', icon: 'inv(A)', description: 'Compute matrix inverse', parameters: 'none' },
      { name: 'Selector', icon: 'Select', description: 'Select elements from vector by index', parameters: 'indices' },
      { name: 'Assignment', icon: 'Assign', description: 'Assign values to specific indices', parameters: 'indices' },
      { name: 'Concatenate', icon: '[A;B]', description: 'Concatenate multiple vectors', parameters: 'numInputs, mode' },
      { name: 'Matrix Sum', icon: 'sum()', description: 'Sum all elements of vector/matrix', parameters: 'none' },
      { name: 'Vector Norm', icon: '||x||', description: 'Compute norm (1, 2, or inf)', parameters: 'normType' },
    ],
  },
  controlDesign: {
    title: 'Control Design',
    description: 'Control system design blocks',
    blocks: [
      { name: 'PID Controller', icon: 'PID', description: 'Continuous PID controller', parameters: 'Kp, Ki, Kd, N, initialConditionI' },
      { name: 'Discrete PID', icon: 'PID_d', description: 'Discrete PID controller', parameters: 'Kp, Ki, Kd, N, sampleTime, method' },
      { name: 'LQR Controller', icon: 'LQR', description: 'Optimal state feedback u = -K*x', parameters: 'K' },
      { name: 'Pole Placement', icon: 'Poles', description: 'State feedback with pole placement', parameters: 'K' },
      { name: 'Lead-Lag Compensator', icon: 'Lead/Lag', description: 'K*(s+z)/(s+p) compensator', parameters: 'K, zero, pole' },
      { name: 'PI Controller', icon: 'PI', description: 'Proportional-Integral controller', parameters: 'Kp, Ki' },
      { name: 'PD Controller', icon: 'PD', description: 'Proportional-Derivative controller', parameters: 'Kp, Kd, N' },
      { name: 'Anti-Windup PID', icon: 'PID+AW', description: 'PID with back-calculation anti-windup', parameters: 'Kp, Ki, Kd, N, Kb, limits' },
      { name: 'Model Reference', icon: 'Ref', description: 'Reference model for adaptive control', parameters: 'A, B, C, D, initialState' },
    ],
  },
  aerospace: {
    title: 'Aerospace Blockset',
    description: 'Aerospace-specific blocks for flight dynamics and navigation',
    blocks: [
      { name: 'Quaternion Normalize', icon: 'q/|q|', description: 'Normalize quaternion to unit length', parameters: 'none' },
      { name: 'Quaternion Multiply', icon: 'q1*q2', description: 'Hamilton product of two quaternions', parameters: 'none' },
      { name: 'Quaternion Conjugate', icon: 'q*', description: 'Compute quaternion conjugate', parameters: 'none' },
      { name: 'Quaternion to Euler', icon: 'q->E', description: 'Convert quaternion to Euler angles', parameters: 'sequence' },
      { name: 'Euler to Quaternion', icon: 'E->q', description: 'Convert Euler angles to quaternion', parameters: 'sequence' },
      { name: 'Quaternion Rotate Vector', icon: 'qvq*', description: 'Rotate 3D vector by quaternion', parameters: 'none' },
      { name: 'DCM to Quaternion', icon: 'DCM->q', description: 'Convert Direction Cosine Matrix to quaternion', parameters: 'none' },
      { name: 'Quaternion to DCM', icon: 'q->DCM', description: 'Convert quaternion to Direction Cosine Matrix', parameters: 'none' },
      { name: 'ISA Atmosphere', icon: 'ISA', description: 'International Standard Atmosphere model', parameters: 'none' },
      { name: '6-DOF (Euler)', icon: '6DOF', description: '6 degrees of freedom rigid body dynamics', parameters: 'mass, inertia, initial states' },
      { name: 'Flat Earth Gravity', icon: 'g', description: 'Constant gravity model', parameters: 'g' },
      { name: 'WGS84 Gravity', icon: 'WGS84', description: 'Gravity varying with latitude and altitude', parameters: 'none' },
    ],
  },
}

// Keyboard shortcuts data
const shortcuts = {
  general: [
    { keys: 'Ctrl+S', action: 'Save model' },
    { keys: 'Ctrl+Z', action: 'Undo' },
    { keys: 'Ctrl+Y', action: 'Redo' },
    { keys: 'Ctrl+Shift+Z', action: 'Redo (alternative)' },
    { keys: 'Escape', action: 'Exit subsystem / Deselect' },
  ],
  editing: [
    { keys: 'Ctrl+A', action: 'Select all blocks' },
    { keys: 'Ctrl+C', action: 'Copy selected blocks' },
    { keys: 'Ctrl+V', action: 'Paste blocks' },
    { keys: 'Delete', action: 'Delete selected blocks' },
    { keys: 'Backspace', action: 'Delete selected blocks' },
  ],
  signals: [
    { keys: 'Right-click line', action: 'Open signal context menu (rename, delete, etc.)' },
    { keys: 'Ctrl+Shift+S', action: 'Highlight signal to source' },
    { keys: 'Ctrl+Shift+D', action: 'Highlight signal to destination' },
    { keys: 'Ctrl+Shift+H', action: 'Clear signal highlighting' },
    { keys: 'Alt + drag', action: 'Fine-grained routing (1px grid)' },
  ],
  layout: [
    { keys: 'Space', action: 'Fit view to content' },
    { keys: 'Ctrl+R', action: 'Rotate selected blocks 90°' },
    { keys: 'Ctrl+]', action: 'Spread blocks apart (5%)' },
    { keys: 'Ctrl+[', action: 'Retract blocks closer (5%)' },
  ],
  navigation: [
    { keys: 'Mouse wheel', action: 'Zoom in/out' },
    { keys: 'Click + drag', action: 'Pan view' },
    { keys: 'Double-click subsystem', action: 'Enter subsystem' },
  ],
}

function ShortcutKey({ children }: { children: string }) {
  return (
    <kbd className="px-2 py-1 bg-editor-bg border border-editor-border rounded text-xs font-mono">
      {children}
    </kbd>
  )
}

function ShortcutRow({ keys, action }: { keys: string; action: string }) {
  return (
    <tr className="border-b border-editor-border/50">
      <td className="py-2 pr-4">
        <ShortcutKey>{keys}</ShortcutKey>
      </td>
      <td className="py-2 text-gray-300">{action}</td>
    </tr>
  )
}

function ShortcutsTab() {
  return (
    <div className="space-y-6">
      {/* General */}
      <div>
        <h3 className="text-sm font-semibold text-blue-400 uppercase mb-3">General</h3>
        <table className="w-full">
          <tbody>
            {shortcuts.general.map((s) => (
              <ShortcutRow key={s.keys} keys={s.keys} action={s.action} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Editing */}
      <div>
        <h3 className="text-sm font-semibold text-blue-400 uppercase mb-3">Selection & Editing</h3>
        <table className="w-full">
          <tbody>
            {shortcuts.editing.map((s) => (
              <ShortcutRow key={s.keys} keys={s.keys} action={s.action} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Signal Lines */}
      <div>
        <h3 className="text-sm font-semibold text-blue-400 uppercase mb-3">Signal Lines</h3>
        <table className="w-full">
          <tbody>
            {shortcuts.signals.map((s) => (
              <ShortcutRow key={s.keys} keys={s.keys} action={s.action} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Layout */}
      <div>
        <h3 className="text-sm font-semibold text-blue-400 uppercase mb-3">View & Layout</h3>
        <table className="w-full">
          <tbody>
            {shortcuts.layout.map((s) => (
              <ShortcutRow key={s.keys} keys={s.keys} action={s.action} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Navigation */}
      <div>
        <h3 className="text-sm font-semibold text-blue-400 uppercase mb-3">Navigation</h3>
        <table className="w-full">
          <tbody>
            {shortcuts.navigation.map((s) => (
              <ShortcutRow key={s.keys} keys={s.keys} action={s.action} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function BlockReferenceTab() {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null)

  const toggleCategory = (key: string) => {
    setExpandedCategory(expandedCategory === key ? null : key)
  }

  return (
    <div className="space-y-2">
      <p className="text-gray-400 text-sm mb-4">
        LibreSim includes 110+ simulation blocks. Click a category to view blocks.
      </p>
      {Object.entries(blockReference).map(([key, category]) => (
        <div key={key} className="border border-editor-border rounded overflow-hidden">
          <button
            onClick={() => toggleCategory(key)}
            className="w-full flex items-center justify-between px-3 py-2 bg-editor-bg hover:bg-editor-border transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="text-blue-400 font-medium">{category.title}</span>
              <span className="text-gray-500 text-sm">({category.blocks.length} blocks)</span>
            </div>
            <svg
              className={`w-4 h-4 text-gray-400 transition-transform ${expandedCategory === key ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedCategory === key && (
            <div className="p-3 bg-editor-surface border-t border-editor-border">
              <p className="text-gray-400 text-sm mb-3">{category.description}</p>
              <div className="space-y-2">
                {category.blocks.map((block) => (
                  <div key={block.name} className="flex items-start gap-3 py-1.5 border-b border-editor-border/30 last:border-0">
                    <span className="flex-shrink-0 w-8 h-6 flex items-center justify-center bg-blue-900/30 rounded text-xs text-blue-300 font-mono">
                      {block.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline gap-2">
                        <span className="text-white font-medium text-sm">{block.name}</span>
                      </div>
                      <p className="text-gray-400 text-xs">{block.description}</p>
                      {block.parameters !== 'none' && (
                        <p className="text-gray-500 text-xs mt-0.5">
                          <span className="text-gray-600">Parameters:</span> {block.parameters}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function AboutTab() {
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!content && !loading) {
      setLoading(true)
      setError(null)
      api.getProjectReadme()
        .then((readme) => {
          setContent(readme)
          setLoading(false)
        })
        .catch((err) => {
          console.error('Failed to load project README:', err)
          setError('Failed to load documentation. Please try again.')
          setLoading(false)
        })
    }
  }, [content, loading])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-400">Loading documentation...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="text-red-400 mb-4">{error}</div>
        <button
          onClick={() => {
            setContent('')
            setError(null)
          }}
          className="text-blue-400 hover:text-blue-300"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="prose prose-invert prose-sm max-w-none
      prose-headings:text-blue-400 prose-headings:font-semibold prose-headings:mt-6 prose-headings:mb-3
      prose-h1:text-xl prose-h2:text-lg prose-h3:text-base
      prose-p:text-gray-300 prose-p:my-2
      prose-a:text-blue-400 prose-a:no-underline hover:prose-a:text-blue-300
      prose-strong:text-white prose-strong:font-semibold
      prose-code:text-green-400 prose-code:bg-gray-800 prose-code:px-1 prose-code:rounded prose-code:text-xs
      prose-ul:text-gray-300 prose-ul:my-2 prose-li:my-0.5
      prose-ol:text-gray-300 prose-ol:my-2
      prose-table:text-sm prose-table:my-3
      prose-th:text-gray-400 prose-th:font-medium prose-th:py-2 prose-th:px-2 prose-th:text-left prose-th:border-b prose-th:border-editor-border
      prose-td:py-1.5 prose-td:px-2 prose-td:text-gray-300 prose-td:border-b prose-td:border-editor-border/50
      prose-hr:border-editor-border prose-hr:my-4
      prose-pre:bg-gray-800 prose-pre:text-gray-300 prose-pre:text-xs prose-pre:p-3 prose-pre:rounded
    ">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  )
}

export function HelpModal() {
  const { showHelpModal, helpModalTab, closeHelpModal, openHelpModal } = useUIStore()
  const [activeTab, setActiveTab] = useState<'shortcuts' | 'about' | 'blocks'>(helpModalTab)

  // Sync tab with store when modal opens
  useEffect(() => {
    if (showHelpModal) {
      setActiveTab(helpModalTab)
    }
  }, [showHelpModal, helpModalTab])

  if (!showHelpModal) return null

  const handleClose = () => {
    closeHelpModal()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleClose()
    }
  }

  const handleTabChange = (tab: 'shortcuts' | 'about' | 'blocks') => {
    setActiveTab(tab)
    openHelpModal(tab)
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100]"
      onClick={handleClose}
      onKeyDown={handleKeyDown}
    >
      <div
        className="bg-editor-surface border border-editor-border rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header with tabs */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-editor-border">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold">Help</h2>
            <div className="flex gap-1">
              <button
                onClick={() => handleTabChange('shortcuts')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  activeTab === 'shortcuts'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-editor-border'
                }`}
              >
                Shortcuts
              </button>
              <button
                onClick={() => handleTabChange('blocks')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  activeTab === 'blocks'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-editor-border'
                }`}
              >
                Blocks
              </button>
              <button
                onClick={() => handleTabChange('about')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  activeTab === 'about'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-editor-border'
                }`}
              >
                About
              </button>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1">
          {activeTab === 'shortcuts' && <ShortcutsTab />}
          {activeTab === 'blocks' && <BlockReferenceTab />}
          {activeTab === 'about' && <AboutTab />}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center px-4 py-3 border-t border-editor-border text-sm text-gray-500">
          <span>Press Escape to close</span>
          <a
            href="https://github.com/masonnixon/LibreSim"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 transition-colors"
          >
            View on GitHub
          </a>
        </div>
      </div>
    </div>
  )
}
