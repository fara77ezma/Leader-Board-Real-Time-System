from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.orm import Session
from config.db import get_db
from controllers.websocket import connect_to_ws

router = APIRouter()


@router.websocket("/ws/{game_name}")
async def leaderboard_ws(
    websocket: WebSocket, game_name: str, db: Session = Depends(get_db)
):
    await connect_to_ws(websocket=websocket, game_name=game_name, db=db)
