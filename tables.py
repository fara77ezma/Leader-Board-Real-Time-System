class Users:
    def __init__(self):
        self.table_name = "users"
        self.columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_code": "TEXT NOT NULL UNIQUE",
            "username": "TEXT NOT NULL UNIQUE",
            "email": "TEXT NOT NULL UNIQUE",
            "password_hash": "TEXT NOT NULL",
            "phone_number": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }

class Leaderboard:
    def __init__(self):
        self.table_name = "leaderboard"
        self.columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "user_code": "TEXT NOT NULL",
            "score": "INTEGER NOT NULL",
            "game_id": "TEXT NOT NULL",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "FOREIGN KEY(user_code)": "REFERENCES users(user_code)"
        }    
