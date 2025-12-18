import hashlib
from http.client import HTTPException
import uuid
from db.db import Base,engine, get_db
from fastapi import FastAPI
from request import RegisterRequest
from routes import users
from sqlalchemy.orm import Session
from db.tables import User


app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hi By Farah"}



app.include_router(users.router)
