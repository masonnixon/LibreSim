import type { BlockDefinition } from '../types/block'

export const routingBlocks: BlockDefinition[] = [
  {
    type: 'mux',
    category: 'routing',
    name: 'Mux',
    description: 'Combine signals into vector',
    inputs: [
      { name: 'in1', dataType: 'double', dimensions: [1] },
      { name: 'in2', dataType: 'double', dimensions: [1] },
    ],
    outputs: [{ name: 'out', dataType: 'double', dimensions: [2] }],
    parameters: [
      {
        name: 'numInputs',
        type: 'number',
        default: 2,
        label: 'Number of Inputs',
        min: 2,
        max: 32,
      },
    ],
    icon: '⋮→',
  },
  {
    type: 'demux',
    category: 'routing',
    name: 'Demux',
    description: 'Split vector into signals',
    inputs: [{ name: 'in', dataType: 'double', dimensions: [2] }],
    outputs: [
      { name: 'out1', dataType: 'double', dimensions: [1] },
      { name: 'out2', dataType: 'double', dimensions: [1] },
    ],
    parameters: [
      {
        name: 'numOutputs',
        type: 'number',
        default: 2,
        label: 'Number of Outputs',
        min: 2,
        max: 32,
      },
    ],
    icon: '→⋮',
  },
  {
    type: 'switch',
    category: 'routing',
    name: 'Switch',
    description: 'Switch between inputs based on control',
    inputs: [
      { name: 'in1', dataType: 'double', dimensions: [1] },
      { name: 'control', dataType: 'double', dimensions: [1] },
      { name: 'in2', dataType: 'double', dimensions: [1] },
    ],
    outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
    parameters: [
      {
        name: 'threshold',
        type: 'number',
        default: 0,
        label: 'Threshold',
        description: 'Control threshold for switching',
      },
      {
        name: 'criteria',
        type: 'select',
        default: 'gte',
        label: 'Criteria',
        options: [
          { value: 'gte', label: 'control >= threshold' },
          { value: 'gt', label: 'control > threshold' },
          { value: 'neq', label: 'control != threshold' },
        ],
      },
    ],
    icon: '⇋',
  },
  {
    type: 'multiport_switch',
    category: 'routing',
    name: 'Multiport Switch',
    description: 'Select from multiple inputs',
    inputs: [
      { name: 'control', dataType: 'double', dimensions: [1] },
      { name: 'in1', dataType: 'double', dimensions: [1] },
      { name: 'in2', dataType: 'double', dimensions: [1] },
    ],
    outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
    parameters: [
      {
        name: 'numDataPorts',
        type: 'number',
        default: 2,
        label: 'Number of Data Ports',
        min: 2,
        max: 32,
      },
      {
        name: 'dataPortOrder',
        type: 'select',
        default: 'one_based',
        label: 'Data Port Indices',
        options: [
          { value: 'zero_based', label: 'Zero-based (0, 1, 2, ...)' },
          { value: 'one_based', label: 'One-based (1, 2, 3, ...)' },
        ],
      },
    ],
    icon: '⇉',
  },
  {
    type: 'goto',
    category: 'routing',
    name: 'Goto',
    description: 'Send signal to From blocks',
    inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
    outputs: [],
    parameters: [
      {
        name: 'tag',
        type: 'string',
        default: 'A',
        label: 'Tag',
        description: 'Identifier for signal routing',
      },
      {
        name: 'visibility',
        type: 'select',
        default: 'local',
        label: 'Tag Visibility',
        options: [
          { value: 'local', label: 'Local' },
          { value: 'scoped', label: 'Scoped' },
          { value: 'global', label: 'Global' },
        ],
      },
    ],
    icon: '[A]',
  },
  {
    type: 'from',
    category: 'routing',
    name: 'From',
    description: 'Receive signal from Goto block',
    inputs: [],
    outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
    parameters: [
      {
        name: 'tag',
        type: 'string',
        default: 'A',
        label: 'Tag',
        description: 'Identifier matching Goto block',
      },
    ],
    icon: '[A]',
  },
]
