from fastapi import FastAPI
from models.tables import Base
from routes import users
from db.db import engine

app = FastAPI()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables ready!")
    
@app.get("/")
def root():
    return {"message": "Hi By Farah"}



app.include_router(users.router)
