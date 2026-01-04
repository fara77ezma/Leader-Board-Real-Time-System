from fastapi import FastAPI
from models.tables import Base
from routes import auth, users, leaderboard
from db.db import engine
from fastapi.security import HTTPBearer


app = FastAPI()

security = HTTPBearer()

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables ready!")
    
@app.get("/")
def root():
    return {"message": "Hi By Farah"}



app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leaderboard.router)