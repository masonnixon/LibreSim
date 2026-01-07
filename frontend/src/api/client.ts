import axios from 'axios'
import type { Model } from '../types/model'
import type { SimulationConfig, SimulationResults } from '../types/simulation'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const api = {
  // Model operations
  async getModels(): Promise<Model[]> {
    const response = await apiClient.get('/models')
    return response.data
  },

  async getModel(id: string): Promise<Model> {
    const response = await apiClient.get(`/models/${id}`)
    return response.data
  },

  async saveModel(model: Model): Promise<Model> {
    if (model.id) {
      const response = await apiClient.put(`/models/${model.id}`, model)
      return response.data
    } else {
      const response = await apiClient.post('/models', model)
      return response.data
    }
  },

  async deleteModel(id: string): Promise<void> {
    await apiClient.delete(`/models/${id}`)
  },

  // Simulation operations
  async validateModel(modelId: string): Promise<{ valid: boolean; errors: string[] }> {
    const response = await apiClient.post(`/models/${modelId}/validate`)
    return response.data
  },

  async compileModel(modelId: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(`/models/${modelId}/compile`)
    return response.data
  },

  async startSimulation(
    model: Model,
    config: SimulationConfig
  ): Promise<{ sessionId: string }> {
    const response = await apiClient.post('/simulate/start', { model, config })
    return response.data
  },

  async stopSimulation(): Promise<void> {
    await apiClient.post('/simulate/stop')
  },

  async resetSimulation(): Promise<{
    success: boolean
    message: string
    currentTime: number
    progress: number
    status: string
  }> {
    const response = await apiClient.post('/simulate/reset')
    return response.data
  },

  async pauseSimulation(): Promise<void> {
    await apiClient.post('/simulate/pause')
  },

  async resumeSimulation(): Promise<void> {
    await apiClient.post('/simulate/resume')
  },

  async getSimulationStatus(): Promise<{ status: string; progress: number; currentTime?: number; error?: string }> {
    const response = await apiClient.get('/simulate/status')
    return response.data
  },

  async getSimulationResults(): Promise<SimulationResults> {
    const response = await apiClient.get('/simulate/results')
    return response.data
  },

  // Step mode simulation operations
  async initStepMode(
    model: Model,
    config: SimulationConfig
  ): Promise<{ success: boolean; sessionId: string; currentTime: number; status: string }> {
    const response = await apiClient.post('/simulate/step/init', { model, config })
    return response.data
  },

  async stepForward(
    numSteps: number = 1
  ): Promise<{
    success: boolean
    stepsExecuted: number
    currentTime: number
    progress: number
    completed: boolean
    status: string
    historySize: number
  }> {
    const response = await apiClient.post('/simulate/step/forward', { numSteps })
    return response.data
  },

  async stepBackward(
    numSteps: number = 1
  ): Promise<{
    success: boolean
    stepsExecuted: number
    currentTime: number
    progress: number
    historySize: number
    status: string
  }> {
    const response = await apiClient.post('/simulate/step/backward', { numSteps })
    return response.data
  },

  async resetStepMode(): Promise<{ success: boolean; currentTime: number; status: string }> {
    const response = await apiClient.post('/simulate/step/reset')
    return response.data
  },

  async continueFromStepMode(): Promise<{ success: boolean; currentTime: number; status: string }> {
    const response = await apiClient.post('/simulate/step/continue')
    return response.data
  },

  async enterStepMode(): Promise<{
    success: boolean
    currentTime: number
    progress: number
    status: string
    historySize: number
  }> {
    const response = await apiClient.post('/simulate/step/enter')
    return response.data
  },

  // Import operations
  async importMDL(file: File): Promise<Model> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post('/import/mdl', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Block library
  async getBlockDefinitions(): Promise<unknown[]> {
    const response = await apiClient.get('/blocks')
    return response.data
  },

  // Documentation
  async getProjectReadme(): Promise<string> {
    const response = await apiClient.get('/docs/readme', {
      responseType: 'text',
      transformResponse: [(data) => data],
    })
    return response.data
  },

  async getExamplesReadme(): Promise<string> {
    const response = await apiClient.get('/docs/examples', {
      responseType: 'text',
      transformResponse: [(data) => data],
    })
    return response.data
  },

  // Examples
  async getExampleList(): Promise<{ id: string; name: string; description: string; category: string }[]> {
    const response = await apiClient.get('/examples')
    return response.data
  },

  async getExample(id: string): Promise<Model> {
    const response = await apiClient.get(`/examples/${id}`)
    return response.data
  },
}

// WebSocket connection for real-time simulation data
export class SimulationWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  constructor(
    private onData: (data: { time: number; signals: Record<string, number> }) => void,
    private onStatus: (status: string, progress: number) => void,
    private onError: (error: string) => void,
    private onConnect: () => void,
    private onDisconnect: () => void
  ) {}

  connect(): void {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/simulation`

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this.onConnect()
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        switch (message.type) {
          case 'data':
            this.onData(message.payload)
            break
          case 'status':
            this.onStatus(message.payload.status, message.payload.progress)
            break
          case 'error':
            this.onError(message.payload.message)
            break
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    this.ws.onerror = () => {
      this.onError('WebSocket connection error')
    }

    this.ws.onclose = () => {
      this.onDisconnect()
      this.attemptReconnect()
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = Math.pow(2, this.reconnectAttempts) * 1000
      setTimeout(() => this.connect(), delay)
    }
  }

  send(message: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}
