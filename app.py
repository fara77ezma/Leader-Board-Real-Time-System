import hashlib
import uuid
from db import create_tables, get_db_connection
from fastapi import FastAPI
from request import RegisterRequest

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hi By Farah"}

@app.on_event("startup")
def startup():
    create_tables()


@app.post("/register")
def root(request: RegisterRequest):
    email = request.email
    username = request.username  
    phone_number = request.phone_number
    password = request.password
    user_code = str(uuid.uuid4()) 

    password_hash = hash_password(password)
    conn,cursor = get_db_connection()
    if cursor is None:
        return {"status": "error", "message": "Database connection failed"}
    cursor.execute(
        "INSERT INTO users (email,user_code, username, phone_number, password_hash) VALUES (%s,%s, %s, %s, %s)",
        (email, username,user_code ,phone_number, password_hash)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "message": "User registered successfully"}


def hash_password(pwd):
    pwd_bytes = pwd.encode('utf-8')
    hashed_pwd = hashlib.sha256(pwd_bytes).hexdigest()
    return hashed_pwd