import mysql.connector
from mysql.connector import Error

def read_secret(path: str) -> str:
    with open(path, "r") as f:
        return f.read().strip()


def get_db_connection():
    try:
        DB_PASSWORD = read_secret("/run/secrets/passwords")

        conn = mysql.connector.connect(
            host="mysql",   # service name from docker-compose
            user="root",
            password=DB_PASSWORD,
            database="leaderboard_db",
            port = 3306
        )
        cursor = conn.cursor() 
        return conn,cursor
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None,None

def create_tables():
    conn, cursor = get_db_connection()
    if not conn:
        return

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_code VARCHAR(36) NOT NULL UNIQUE,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            phone_number VARCHAR(15),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_code VARCHAR(36) NOT NULL,
            score INT NOT NULL,
            game_id VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_user
                FOREIGN KEY (user_code)
                REFERENCES users(user_code)
                ON DELETE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
