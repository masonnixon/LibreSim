import type { BlockInstance, Connection } from './block'
import type { SimulationConfig } from './simulation'

export interface ModelMetadata {
  name: string
  description: string
  author: string
  createdAt: string
  modifiedAt: string
  version: string
}

export interface Model {
  id: string
  metadata: ModelMetadata
  blocks: BlockInstance[]
  connections: Connection[]
  simulationConfig: SimulationConfig
}

export interface Project {
  id: string
  name: string
  description: string
  models: Model[]
  createdAt: string
  modifiedAt: string
}
