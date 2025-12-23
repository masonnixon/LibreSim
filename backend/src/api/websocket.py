"""WebSocket handler for real-time simulation data."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Connected clients
connected_clients: set[WebSocket] = set()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        message_json = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client."""
        await websocket.send_text(json.dumps(message))


manager = ConnectionManager()


@router.websocket("/ws/simulation")
async def websocket_simulation(websocket: WebSocket):
    """WebSocket endpoint for simulation data streaming."""
    await manager.connect(websocket)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "subscribe":
                # Client wants to subscribe to simulation data
                await manager.send_personal(websocket, {
                    "type": "subscribed",
                    "payload": {"message": "Subscribed to simulation updates"}
                })

            elif message.get("type") == "parameter_update":
                # Handle runtime parameter update
                # This would interact with the simulation runner
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


async def broadcast_simulation_data(time: float, signals: dict):
    """Broadcast simulation data to all connected clients."""
    await manager.broadcast({
        "type": "data",
        "payload": {
            "time": time,
            "signals": signals
        }
    })


async def broadcast_simulation_status(status: str, progress: float, current_time: float):
    """Broadcast simulation status to all connected clients."""
    await manager.broadcast({
        "type": "status",
        "payload": {
            "status": status,
            "progress": progress,
            "currentTime": current_time
        }
    })


async def broadcast_simulation_error(error: str):
    """Broadcast simulation error to all connected clients."""
    await manager.broadcast({
        "type": "error",
        "payload": {
            "message": error
        }
    })
