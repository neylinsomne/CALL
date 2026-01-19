"""
WebSocket Connection Manager
Handles multiple WebSocket connections for real-time audio streaming
"""

from typing import Dict, Optional
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for conversations"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, conversation_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[conversation_id] = websocket
        
    def disconnect(self, conversation_id: str):
        """Remove a WebSocket connection"""
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]
            
    def get_connection(self, conversation_id: str) -> Optional[WebSocket]:
        """Get a WebSocket connection by conversation ID"""
        return self.active_connections.get(conversation_id)
        
    async def send_json(self, conversation_id: str, data: dict):
        """Send JSON data to a specific connection"""
        websocket = self.active_connections.get(conversation_id)
        if websocket:
            await websocket.send_json(data)
            
    async def send_bytes(self, conversation_id: str, data: bytes):
        """Send binary data to a specific connection"""
        websocket = self.active_connections.get(conversation_id)
        if websocket:
            await websocket.send_bytes(data)
            
    async def broadcast(self, data: dict):
        """Send data to all connections"""
        for websocket in self.active_connections.values():
            await websocket.send_json(data)
