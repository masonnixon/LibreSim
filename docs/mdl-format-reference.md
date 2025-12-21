# Simulink MDL File Format Reference

This document provides a reference for the Simulink MDL file format, focusing on block parameters and property names used when importing MDL files into LibreSim.

## Overview

MDL (Model) files are text-based files used by older versions of Simulink (pre-2012). They contain hierarchical block and system definitions with parameters. The newer SLX format (introduced in Simulink 2012) is XML-based but can be converted to MDL format.

## MDL File Structure

```
Model {
  Name                  "modelname"
  Version               8.0
  StartTime             "0.0"
  StopTime              "10.0"
  Solver                "ode45"
  FixedStep             "0.01"

  System {
    Name                "modelname"

    Block {
      BlockType         Constant
      Name              "Constant1"
      Position          [100, 100, 130, 130]
      Value             "1"
    }

    Line {
      SrcBlock          "Constant1"
      SrcPort           1
      DstBlock          "Scope"
      DstPort           1
    }
  }
}
```

## Block Parameter Reference

### Constant Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `Value` | Constant output value | `1` | `value` |
| `VectorParams1D` | Interpret vectors as 1-D | `on` | - |
| `SampleTime` | Sample time | `inf` | - |
| `OutDataTypeStr` | Output data type | `Inherit: auto` | - |

**Example:**
```
Block {
  BlockType           Constant
  Name                "Constant1"
  Value               "5.0"
}
```

### Inport Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `Port` | Position of port on parent block | Sequential | `portNumber` |
| `IconDisplay` | Icon display mode | `Port number` | - |
| `PortDimensions` | Signal dimensions | `-1` (auto) | - |
| `OutDataTypeStr` | Output data type | `Inherit: auto` | - |
| `SignalType` | Signal complexity | `auto` | - |
| `SampleTime` | Sample time | `-1` | - |
| `Interpolate` | Linear interpolation | `on` | - |

**Example:**
```
Block {
  BlockType           Inport
  Name                "In1"
  Port                "1"
}
```

### Outport Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `Port` | Position of port on parent block | Sequential | `portNumber` |
| `IconDisplay` | Icon display mode | `Port number` | - |
| `OutDataTypeStr` | Output data type | `Inherit: auto` | - |

**Example:**
```
Block {
  BlockType           Outport
  Name                "Out1"
  Port                "1"
}
```

### Math Function Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `Operator` | Mathematical function | `exp` | `function` |
| `OutputSignalType` | Output signal type | `auto` | - |

**Operator Values:**
- `exp` - Exponential (e^u)
- `log` - Natural logarithm
- `10^u` - Power of 10
- `log10` - Base-10 logarithm
- `magnitude^2` - Magnitude squared
- `square` - Square (u^2)
- `sqrt` - Square root
- `pow` - Power
- `conj` - Complex conjugate
- `reciprocal` - Reciprocal (1/u)
- `hypot` - Hypotenuse
- `rem` - Remainder
- `mod` - Modulus
- `transpose` - Matrix transpose
- `hermitian` - Hermitian (complex conjugate transpose)

**Example:**
```
Block {
  BlockType           Math
  Name                "Math Function"
  Operator            "exp"
}
```

### Reshape Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `OutputDimensionality` | Output dimensionality mode | `1-D array` | `outputDimensionality` |
| `OutputDimensions` | Custom dimensions (when Customize) | `[1,1]` | `outputDimensions` |

**OutputDimensionality Values:**
- `1-D array` - Output as 1-D array
- `Column vector (2-D)` - Output as column vector
- `Row vector (2-D)` - Output as row vector
- `Customize` - Use OutputDimensions parameter
- `Derive from reference input port` - Match reference input

**Example:**
```
Block {
  BlockType           Reshape
  Name                "Reshape"
  OutputDimensionality "Customize"
  OutputDimensions    "[4, 1]"
}
```

### Gain Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `Gain` | Gain value | `1` | `gain` |
| `Multiplication` | Element/matrix multiplication | `Element-wise` | - |

**Example:**
```
Block {
  BlockType           Gain
  Name                "Gain1"
  Gain                "2.5"
}
```

### Sum Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `Inputs` | Input signs (e.g., `++`, `+-`, `\|++`) | `++` | `signs` |
| `IconShape` | Block shape | `round` | - |

**Example:**
```
Block {
  BlockType           Sum
  Name                "Sum1"
  Inputs              "+-"
}
```

### Mux Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `Inputs` | Number of inputs | `2` | `numInputs` |
| `DisplayOption` | Display mode | `bar` | - |

**Alternative Property Names:**
- `NumberOfInputs`
- `NumInputs`
- `Ports` (array format: `[numInputs]`)

**Example:**
```
Block {
  BlockType           Mux
  Name                "Mux1"
  Inputs              "4"
}
```

### Demux Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `Outputs` | Number of outputs | `2` | `numOutputs` |
| `DisplayOption` | Display mode | `bar` | - |

**Alternative Property Names:**
- `NumberOfOutputs`
- `NumOutputs`
- `Ports` (array format: `[numInputs, numOutputs]`)

**Example:**
```
Block {
  BlockType           Demux
  Name                "Demux1"
  Outputs             "3"
}
```

### Integrator Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `InitialCondition` | Initial state value | `0` | `initialCondition` |
| `LimitOutput` | Enable saturation | `off` | `limitOutput` |
| `UpperSaturationLimit` | Upper saturation limit | `inf` | `upperLimit` |
| `LowerSaturationLimit` | Lower saturation limit | `-inf` | `lowerLimit` |

**Example:**
```
Block {
  BlockType           Integrator
  Name                "Integrator"
  InitialCondition    "0"
}
```

### Transfer Function Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `Numerator` | Numerator coefficients | `[1]` | `numerator` |
| `Denominator` | Denominator coefficients | `[1 1]` | `denominator` |

**Example:**
```
Block {
  BlockType           TransferFcn
  Name                "Transfer Fcn"
  Numerator           "[1]"
  Denominator         "[1 2 1]"
}
```

### Saturation Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `UpperLimit` | Upper saturation limit | `0.5` | `upperLimit` |
| `LowerLimit` | Lower saturation limit | `-0.5` | `lowerLimit` |

**Example:**
```
Block {
  BlockType           Saturate
  Name                "Saturation"
  UpperLimit          "10"
  LowerLimit          "-10"
}
```

### Sine Wave Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `SineType` | Time/sample based | `Time based` | - |
| `Amplitude` | Signal amplitude | `1` | `amplitude` |
| `Frequency` | Frequency (rad/sec) | `1` | `frequency` |
| `Phase` | Phase offset (rad) | `0` | `phase` |
| `Bias` | DC offset | `0` | `bias` |
| `SampleTime` | Sample time | `0` | - |

**Example:**
```
Block {
  BlockType           Sin
  Name                "Sine Wave"
  Amplitude           "1"
  Frequency           "1"
  Phase               "0"
  Bias                "0"
}
```

### Step Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `Time` | Step time | `1` | `stepTime` |
| `Before` | Initial value | `0` | `initialValue` |
| `After` | Final value | `1` | `finalValue` |
| `SampleTime` | Sample time | `0` | - |

**Example:**
```
Block {
  BlockType           Step
  Name                "Step"
  Time                "1"
  Before              "0"
  After               "1"
}
```

### Scope Block

| MDL Property | Description | Default | LibreSim Parameter |
|-------------|-------------|---------|-------------------|
| `NumInputPorts` | Number of input ports | `1` | `numInputs` |
| `SaveName` | Variable name for data | `ScopeData` | - |
| `DataFormat` | Data format | `StructureWithTime` | - |

**Example:**
```
Block {
  BlockType           Scope
  Name                "Scope"
  NumInputPorts       "2"
}
```

## Connection (Line) Format

Connections between blocks are defined using `Line` elements:

```
Line {
  SrcBlock            "BlockName1"
  SrcPort             1
  DstBlock            "BlockName2"
  DstPort             1
  Points              [x1, y1; x2, y2]
}
```

**Properties:**
- `SrcBlock` - Source block name
- `SrcPort` - Source port number (1-indexed)
- `DstBlock` - Destination block name
- `DstPort` - Destination port number (1-indexed)
- `Points` - Optional routing waypoints

## Block Type Mappings

| Simulink BlockType | LibreSim Type |
|-------------------|---------------|
| `Constant` | `constant` |
| `Step` | `step` |
| `Ramp` | `ramp` |
| `Sin` | `sine_wave` |
| `Clock` | `clock` |
| `Scope` | `scope` |
| `Display` | `display` |
| `ToWorkspace` | `to_workspace` |
| `Terminator` | `terminator` |
| `Integrator` | `integrator` |
| `Derivative` | `derivative` |
| `TransferFcn` | `transfer_function` |
| `StateSpace` | `state_space` |
| `Gain` | `gain` |
| `Sum` | `sum` |
| `Product` | `product` |
| `Math` | `math_function` |
| `Abs` | `abs` |
| `Saturate` / `Saturation` | `saturation` |
| `UnitDelay` | `unit_delay` |
| `ZeroOrderHold` | `zero_order_hold` |
| `Mux` | `mux` |
| `Demux` | `demux` |
| `Switch` | `switch` |
| `Goto` | `goto` |
| `From` | `from` |
| `Inport` | `inport` |
| `Outport` | `outport` |
| `SubSystem` | `subsystem` |
| `Reshape` | `reshape` |
| `Reference` | `reference` |

## Resources

- [MathWorks Inport Block Documentation](https://www.mathworks.com/help/simulink/slref/inport.html)
- [MathWorks Constant Block Documentation](https://www.mathworks.com/help/simulink/slref/constant.html)
- [MathWorks Math Function Block Documentation](https://www.mathworks.com/help/simulink/slref/mathfunction.html)
- [MathWorks Reshape Block Documentation](https://www.mathworks.com/help/simulink/slref/reshape.html)
- [Simulink Model Parsing Tools (GitHub)](https://github.com/steventen/Simulink-Model-Parsing-Tools)
- [SLX2MDL Transformation (GitHub)](https://github.com/mdstepha/SLX2MDL)

## Notes for LibreSim MDL Importer

1. **Property names are case-sensitive** in MDL files
2. **Default values** may be omitted in MDL files - blocks may not include properties that match Simulink defaults
3. **Port numbering** is 1-indexed in MDL but converted to 0-indexed in LibreSim
4. **Array values** use space or comma separators: `[1 2 3]` or `[1, 2, 3]`
5. **Quoted strings** are used for values that may contain special characters
6. **Multiple property name variants** may exist for the same parameter (e.g., `Inputs`, `NumberOfInputs`, `NumInputs` for Mux)
