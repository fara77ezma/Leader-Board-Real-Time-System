from fastapi import WebSocket, WebSocketDisconnect

from sqlalchemy.orm import Session

from config.websocket import manager
from controllers import leaderboard


async def connect_to_ws(websocket: WebSocket, game_name: str, db: Session):
    await manager.connect(websocket=websocket, game_name=game_name)
    try:
        current = leaderboard.fetch_leaderboard(game_name=game_name, limit=10, db=db)
        await websocket.send_json(current)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket=websocket, game_name=game_name)
