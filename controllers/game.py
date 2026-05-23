from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.request import CreateGameRequest
from models.tables import Game


def create_new_game(request: CreateGameRequest, db: Session):
    game = db.query(Game).filter(Game.name == request.name).first()
    print(f"Checking if game with name '{request.name}' exists: {game is not None}")
    if game:
        if game.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game with this name already exists.",
            )
        else:
            try:
                game.is_active = True
                db.commit()
                return {"message": "Game reactivated successfully."}
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to reactivate game.",
                )

    else:
        try:
            print(f"Creating new game with name: {request.name}")
            new_game = Game(
                name=request.name,
                description=request.description,
                is_active=request.is_active,
            )
            db.add(new_game)
            print(f"New game added to session: {new_game}")
            db.commit()
            return {"message": "New game created successfully."}
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create new game.",
            )


def get_games(db: Session, is_active: bool = None):
    try:
        if is_active is not None:
            games = db.query(Game).filter(Game.is_active == is_active).all()
        else:
            games = db.query(Game).all()
        return games
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve games.",
        )


def deactivate_game(game_name: str, db: Session):
    game = db.query(Game).filter(Game.name == game_name).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found.",
        )
    if not game.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game is already deactivated.",
        )
    try:
        game.is_active = False
        db.commit()
        return {"message": "Game deactivated successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate game.",
        )


def activate_game(game_name: str, db: Session):
    game = db.query(Game).filter(Game.name == game_name).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found.",
        )
    if game.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game is already active.",
        )
    try:
        game.is_active = True
        db.commit()
        return {"message": "Game activated successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate game.",
        )


def delete_game(game_name: str, db: Session):
    game = db.query(Game).filter(Game.name == game_name).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found.",
        )
    try:
        db.delete(game)
        db.commit()
        return {"message": "Game deleted successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete game.",
        )
