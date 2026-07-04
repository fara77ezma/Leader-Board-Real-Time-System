# System Architecture

This document outlines the system architecture of the Real-Time Leaderboard project.

## 🗄️ Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    USER ||--o{ REFRESH_TOKEN : has
    USER ||--o{ LEADERBOARD_ENTRY : scores
    GAME ||--o{ LEADERBOARD_ENTRY : contains
    
    USER {
        int id PK
        string user_code UK
        string username UK
        string email UK
        string password_hash
        string phone_number
        boolean is_verified
        boolean is_active
        boolean is_admin
        string email_verification_code
        datetime email_verification_expiry
        string password_reset_code
        datetime password_reset_expiry
        string avatar_url
        datetime created_at
        datetime updated_at
    }
    
    GAME {
        int id PK
        string name UK
        string description
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    LEADERBOARD_ENTRY {
        int id PK
        string user_code FK
        int score
        string game_name FK
        datetime created_at
        datetime updated_at
    }
    
    REFRESH_TOKEN {
        int id PK
        int user_id FK
        string refresh_token UK
        boolean is_revoked
        datetime expires_at
        datetime created_at
    }
```

## 🔄 Request-Response Flow

### Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant DB as MySQL
    participant Mail as Email Service
    
    Client->>API: POST /auth/register
    API->>DB: Save user + generate verification code
    DB-->>API: User created
    API->>Mail: Send verification email
    Mail-->>Client: Email delivered
    
    Client->>API: GET /auth/verify-email?code=xxx
    API->>DB: Verify code & mark user verified
    DB-->>API: User verified
    API-->>Client: Verification confirmed
    
    Client->>API: POST /auth/login
    API->>DB: Query user + verify password hash
    DB-->>API: User found
    API-->>Client: JWT access token + Refresh token
    
    Note over Client,API: On subsequent requests, JWT is verified<br/>locally using the secret key — no DB lookup needed
```

### Score Submission & Real-time Update Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant DB as MySQL
    participant Redis as Redis
    participant CM as ConnectionManager
    participant WS as Connected WebSocket Clients
    
    Client->>API: POST /leaderboard/submit-score
    API->>DB: Insert score record (source of truth)
    DB-->>API: Score saved
    API->>Redis: ZADD leaderboard:{game} user_id score
    Note over Redis: Only updated if new score beats personal best
    Redis-->>API: Sorted set updated
    API->>CM: Fetch updated top-10
    CM->>Redis: ZREVRANGE leaderboard:{game} 0 9
    Redis-->>CM: Top 10 entries
    CM->>WS: send_json to all active connections for this game
    API-->>Client: Score accepted + current rank
```

## 🏗️ Layered Architecture

```
┌─────────────────────────────────────────────────────┐
│              PRESENTATION LAYER                      │
│   routes/auth.py  routes/game.py  routes/users.py   │
│   routes/leaderboard.py  routes/websocket.py        │
├─────────────────────────────────────────────────────┤
│              APPLICATION LAYER                       │
│  controllers/auth.py  controllers/game.py           │
│  controllers/users.py  controllers/leaderboard.py   │
│  controllers/websocket.py                           │
├─────────────────────────────────────────────────────┤
│              DOMAIN LAYER                            │
│  models/tables.py (SQLAlchemy ORM models)           │
│  models/request.py  models/response.py (Pydantic)   │
├─────────────────────────────────────────────────────┤
│              INFRASTRUCTURE LAYER                    │
│  config/db.py (MySQL + connection pool)             │
│  config/redis.py (sync + async Redis clients)       │
│  config/websocket.py (ConnectionManager)            │
│  config/cloudinary.py  config/mail.py              │
└─────────────────────────────────────────────────────┘
```

## 🔐 Security Architecture

```mermaid
graph LR
    User["👤 User"]
    Creds["🔑 Credentials"]
    Hash["🔐 Bcrypt Hash\n(12 rounds)"]
    JWT["🎟️ JWT Access Token\n(verified locally\nvia secret key)"]
    RT["🔄 Refresh Token\n(stored in MySQL)"]
    DB["🗄️ MySQL"]
    RL["🚦 Rate Limiter\n(Redis-backed)"]

    User -->|username + password| Creds
    Creds -->|verify against| Hash
    Hash -->|stored in| DB
    Hash -->|if valid, issue| JWT
    Hash -->|if valid, issue| RT
    RT -->|stored & revoked in| DB
    JWT -->|verified on each request\nusing SECRET_KEY| JWT
    DB -->|check is_admin for admin routes| User
    User -->|auth endpoints| RL
```

## 🔄 WebSocket Architecture

```
Client A ──WS connect──▶ /ws/{game_name}
Client B ──WS connect──▶ /ws/{game_name}
Client C ──WS connect──▶ /ws/{game_name}
                              │
                              ▼
                    ConnectionManager
                  { game_name: [A, B, C] }
                              │
                   on new high score:
                              │
                    Redis ZREVRANGE ──▶ top 10
                              │
                    send_json to A, B, C
```

The `ConnectionManager` is an in-memory dict mapping game names to lists of active WebSocket connections. When a new high score lands, the leaderboard controller fetches the updated top 10 from Redis and the manager broadcasts it directly to all connected clients for that game.