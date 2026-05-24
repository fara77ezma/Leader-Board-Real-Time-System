from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str,list[WebSocket]] = {}
        
    async def connect(self, game_name: str, websocket: WebSocket):
        await websocket.accept()
        if game_name not in self.active_connections:
            self.active_connections[game_name] = []
        self.active_connections[game_name].append(websocket)
        
    async def disconnect(self, game_name: str, websocket: WebSocket):
        await websocket.close()
        if game_name in self.active_connections:
            self.active_connections[game_name].remove(websocket)
            if not self.active_connections[game_name]:
                del self.active_connections[game_name]
         
    async def prodcast(self, game_name:str, data:dict):
        if game_name in self.active_connections:
            for connection in self.active_connections[game_name]:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    await self.disconnect(self,game_name,connection)