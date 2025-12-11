import type { BlockDefinition } from '../types/block'

export const subsystemBlocks: BlockDefinition[] = [
  {
    type: 'subsystem',
    category: 'subsystems',
    name: 'Subsystem',
    description: 'Group of blocks that can be collapsed into a single block',
    inputs: [],  // Dynamic based on internal Inport blocks
    outputs: [], // Dynamic based on internal Outport blocks
    parameters: [
      {
        name: 'description',
        type: 'string',
        default: '',
        label: 'Description',
        description: 'Description of what this subsystem does',
      },
    ],
    icon: '{ }',
  },
  {
    type: 'inport',
    category: 'subsystems',
    name: 'Inport',
    description: 'Input port for subsystem - receives signal from parent level',
    inputs: [],
    outputs: [{ name: 'out', dataType: 'double', dimensions: [1] }],
    parameters: [
      {
        name: 'portNumber',
        type: 'number',
        default: 1,
        label: 'Port Number',
        description: 'Port number on the subsystem block',
        min: 1,
        max: 32,
      },
    ],
    icon: '>',
  },
  {
    type: 'outport',
    category: 'subsystems',
    name: 'Outport',
    description: 'Output port for subsystem - sends signal to parent level',
    inputs: [{ name: 'in', dataType: 'double', dimensions: [1] }],
    outputs: [],
    parameters: [
      {
        name: 'portNumber',
        type: 'number',
        default: 1,
        label: 'Port Number',
        description: 'Port number on the subsystem block',
        min: 1,
        max: 32,
      },
    ],
    icon: '<',
  },
]
