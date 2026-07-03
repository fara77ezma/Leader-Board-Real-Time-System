# System Architecture

This document outlines the system architecture of the Real-time Leaderboard project.

## 🏛️ High-Level Architecture

```mermaid
graph TB
    Client["🖥️ Client Applications"]
    API["⚡ FastAPI Server<br/>(uvicorn)"]
    WS["🔌 WebSocket Handler"]
    Auth["🔐 Authentication<br/>JWT + Refresh Tokens"]
    
    DB[(🗄️ MySQL/PostgreSQL<br/>SQLAlchemy ORM)]
    Redis["📕 Redis<br/>Caching & Pub/Sub"]
    Email["📧 Email Service<br/>FastAPI-Mail"]
    Cloud["☁️ Cloudinary<br/>Image Storage"]
    
    Client -->|REST API| API
    Client -->|WebSocket| WS
    
    API -->|Auth Flow| Auth
    Auth -->|Query/Update| DB
    
    API -->|Cache| Redis
    API -->|Real-time Events| WS
    WS -->|Pub/Sub| Redis
    
    API -->|Verify Email| Email
    API -->|Upload Avatar| Cloud
    API -->|Store User Data| DB
    API -->|Score Updates| Redis
    API -->|Leaderboard| DB
```

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
    participant DB as Database
    participant Mail as Email Service
    
    Client->>API: POST /auth/register
    API->>DB: Save user + generate verification code
    DB-->>API: User created
    API->>Mail: Send verification email
    Mail-->>Client: Email sent
    
    Client->>API: GET /auth/verify-email?code=xxx
    API->>DB: Verify code & mark user verified
    DB-->>API: User verified
    
    Client->>API: POST /auth/login
    API->>DB: Query user + verify password
    DB-->>API: User found
    API-->>Client: JWT token + Refresh token
```

### Score Submission & Real-time Update Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Redis as Redis Cache
    participant DB as Database
    participant WS as WebSocket Server
    
    Client->>API: POST /leaderboard/score
    API->>DB: Insert score record
    DB-->>API: Score saved
    API->>Redis: Update cached leaderboard
    Redis-->>API: Cache updated
    API->>WS: Publish score update
    WS->>Redis: Pub/Sub event
    WS-->>Client: Broadcast to all connected clients
    
    Client->>API: GET /leaderboard/game_name
    API->>Redis: Query cached leaderboard
    Redis-->>API: Return top scores
    API-->>Client: Leaderboard data
```

## 🏗️ Layered Architecture

```
┌─────────────────────────────────────┐
│      🖥️  PRESENTATION LAYER         │
│   (FastAPI Routes & Endpoints)      │
├─────────────────────────────────────┤
│      🎮 APPLICATION LAYER           │
│   (Controllers & Business Logic)    │
├─────────────────────────────────────┤
│      📦 DOMAIN LAYER                │
│   (Models & Data Transfer Objects)  │
├─────────────────────────────────────┤
│      💾 PERSISTENCE LAYER           │
│  (Database & Cache Operations)      │
└─────────────────────────────────────┘
```

## 📂 Component Structure

### Routes Layer
Handles HTTP requests and WebSocket connections
- `auth.py` - Authentication endpoints
- `users.py` - User management endpoints
- `game.py` - Game CRUD endpoints
- `leaderboard.py` - Leaderboard query endpoints
- `websocket.py` - Real-time connection endpoints

### Controllers Layer
Contains business logic and data validation
- `auth.py` - Authentication logic, token generation
- `users.py` - User operations, validation
- `game.py` - Game creation, activation logic
- `leaderboard.py` - Score processing, ranking
- `websocket.py` - Real-time event handlers

### Models Layer
Defines data structures
- `tables.py` - SQLAlchemy ORM models (User, Game, LeaderboardEntry, RefreshToken)
- `request.py` - Pydantic request schemas for validation
- `response.py` - Pydantic response schemas for serialization

### Config Layer
External service configurations
- `db.py` - Database connection pool & session management
- `redis.py` - Redis sync & async clients
- `mail.py` - Email service configuration
- `websocket.py` - WebSocket connection manager
- `cloudinary.py` - Image upload service

## 🔐 Security Architecture

```mermaid
graph LR
    User["👤 User"]
    Creds["🔑 Credentials"]
    Hash["🔐 Bcrypt Hash"]
    JWT["🎟️ JWT Token"]
    Redis["📕 Token Cache"]
    DB["🗄️ Database"]
    
    User -->|username/password| Creds
    Creds -->|hash & compare| Hash
    Hash -->|if valid| JWT
    JWT -->|store for revocation| Redis
    JWT -->|verify| DB
    DB -->|check is_admin| User
```

## ⚡ Performance Optimization

### Caching Strategy
- **Redis Sorted Sets:** Leaderboard rankings
- **Redis Strings:** User session data
- **Database Indexes:** On frequently queried columns (username, user_code, game_name)

### Database Optimization
- Connection pooling with SQLAlchemy
- Foreign key relationships with CASCADE deletion
- Pagination for large result sets
- Query optimization with selective field loading

### Real-time Optimization
- WebSocket pub/sub for efficient broadcasting
- Async Redis for non-blocking operations
- Event-driven architecture for score updates

## 📊 Data Flow Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        Web["Web Browser"]
        Mobile["Mobile App"]
    end
    
    subgraph "API Layer"
        REST["REST API"]
        WS["WebSocket Server"]
    end
    
    subgraph "Business Logic"
        Auth["Auth Controller"]
        Game["Game Controller"]
        LB["Leaderboard Controller"]
    end
    
    subgraph "Data Layer"
        DB[(Database)]
        Cache["Redis Cache"]
    end
    
    subgraph "External Services"
        Email["📧 Email"]
        CDN["☁️ CDN"]
    end
    
    Web -->|REST| REST
    Mobile -->|REST| REST
    Web -->|WS| WS
    Mobile -->|WS| WS
    
    REST --> Auth
    REST --> Game
    REST --> LB
    WS --> LB
    
    Auth --> DB
    Game --> DB
    LB --> Cache
    Cache --> DB
    
    Auth --> Email
    REST --> CDN
```

## 🔄 Deployment Architecture (Docker Compose)

```mermaid
graph TB
    subgraph "Docker Compose"
        subgraph "Services"
            App["🐍 Python App<br/>FastAPI + Uvicorn"]
            Database["🗄️ MySQL/PostgreSQL<br/>Container"]
            Cache["📕 Redis<br/>Container"]
            Mailhog["📧 Mailhog<br/>Mock Email"]
        end
        
        subgraph "Networks"
            Network["internal<br/>network"]
        end
        
        subgraph "Volumes"
            DBVol["db_data"]
            AppVol["app_code"]
        end
    end
    
    Client["🖥️ Client<br/>localhost:8000"]
    
    Client -->|:8000| App
    App -->|internal| Database
    App -->|internal| Cache
    App -->|internal| Mailhog
    
    Database -.->|persist| DBVol
    App -.->|mount| AppVol
```

## 🔄 API Request Pipeline

```
Request
   ↓
[1] Route Handler (routes/*.py)
   ↓
[2] Authentication Check (JWT verification)
   ↓
[3] Authorization Check (role-based access)
   ↓
[4] Input Validation (Pydantic schemas)
   ↓
[5] Controller Logic (controllers/*.py)
   ↓
[6] Cache Check (Redis)
   ↓
[7] Database Query (SQLAlchemy)
   ↓
[8] Response Serialization (Pydantic models)
   ↓
Response → Client
```

## 🧵 Concurrency Model

- **FastAPI:** Async I/O with uvicorn workers
- **Database:** Connection pooling (default pool_size=20)
- **Redis:** Async client for non-blocking operations
- **WebSocket:** Async message handling with asyncio
- **Task Scheduling:** APScheduler for background tasks

## 🎯 Key Design Patterns

1. **Repository Pattern:** Database queries abstracted in controllers
2. **Service Layer:** Business logic centralized in controllers
3. **Dependency Injection:** FastAPI's `Depends()` for resource management
4. **Factory Pattern:** Redis client initialization
5. **Observer Pattern:** WebSocket pub/sub for real-time updates
6. **Circuit Breaker:** Graceful error handling in health checks

## 🚀 Scalability Considerations

### Horizontal Scaling
- Stateless API servers (state in Redis/Database)
- Load balancer ready (all clients connect to same endpoints)
- Database replica support

### Vertical Scaling
- Connection pooling for database
- Redis memory optimization
- Async I/O for high concurrency

### Monitoring
- Health check endpoint at `/health`
- Application logging
- Database performance monitoring

---

**For more details on specific components, refer to the source code and inline documentation.**
