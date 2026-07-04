# System Architecture

This document outlines the system architecture of the Real-time Leaderboard project.

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