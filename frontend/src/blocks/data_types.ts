import type { BlockDefinition } from '../types/block'

export const dataTypeBlocks: BlockDefinition[] = [
  {
    type: 'data_type_conversion',
    category: 'data_types',
    name: 'Data Type Conversion',
    description: 'Convert signal to a different data type',
    inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
    outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
    parameters: [
      {
        name: 'outputType',
        type: 'select',
        default: 'double',
        label: 'Output Data Type',
        options: [
          { value: 'double', label: 'double' },
          { value: 'single', label: 'single' },
          { value: 'int8', label: 'int8' },
          { value: 'int16', label: 'int16' },
          { value: 'int32', label: 'int32' },
          { value: 'uint8', label: 'uint8' },
          { value: 'uint16', label: 'uint16' },
          { value: 'uint32', label: 'uint32' },
          { value: 'boolean', label: 'boolean' },
        ],
      },
      {
        name: 'saturationMode',
        type: 'select',
        default: 'wrap',
        label: 'Saturation Mode',
        options: [
          { value: 'wrap', label: 'Wrap on overflow' },
          { value: 'saturate', label: 'Saturate on overflow' },
        ],
      },
      {
        name: 'roundingMode',
        type: 'select',
        default: 'floor',
        label: 'Rounding Mode',
        options: [
          { value: 'floor', label: 'Floor' },
          { value: 'ceil', label: 'Ceiling' },
          { value: 'round', label: 'Round' },
          { value: 'trunc', label: 'Truncate (towards zero)' },
        ],
      },
    ],
    icon: 'Convert',
  },
  {
    type: 'real_imag_to_complex',
    category: 'data_types',
    name: 'Real-Imag to Complex',
    description: 'Create complex number from real and imaginary parts (outputs magnitude and phase)',
    inputs: [
      { name: 'real', dataType: 'double', dimensions: [1] },
      { name: 'imag', dataType: 'double', dimensions: [1] },
    ],
    outputs: [
      { name: 'magnitude', dataType: 'double', dimensions: [1] },
      { name: 'phase', dataType: 'double', dimensions: [1] },
    ],
    parameters: [],
    icon: 'Re+jIm',
  },
  {
    type: 'complex_to_real_imag',
    category: 'data_types',
    name: 'Complex to Real-Imag',
    description: 'Extract real and imaginary parts from complex number (inputs magnitude and phase)',
    inputs: [
      { name: 'magnitude', dataType: 'double', dimensions: [1] },
      { name: 'phase', dataType: 'double', dimensions: [1] },
    ],
    outputs: [
      { name: 'real', dataType: 'double', dimensions: [1] },
      { name: 'imag', dataType: 'double', dimensions: [1] },
    ],
    parameters: [],
    icon: 'Re,Im',
  },
]
