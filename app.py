from fastapi import FastAPI
from routes import users


app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hi By Farah"}



app.include_router(users.router)
