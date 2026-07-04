# Real-Time Leaderboard System

A FastAPI backend for real-time game leaderboards. Built as a side project to go deeper on Docker, Redis, and WebSockets.

Players register, submit scores, and see live-updating rankings pushed over WebSockets — backed by MySQL for durability and Redis sorted sets for fast ranked reads.

## 🎯 Features

- **User Authentication & Authorization**
  - JWT-based authentication with refresh tokens
  - Email verification with expiring verification codes
  - Password reset functionality
  - Admin role management

- **Game Management**
  - Create, activate, deactivate, and delete games
  - Public active game listing endpoint
  - Admin-only management endpoints

- **Real-time Leaderboard**
  - Live score updates pushed to clients via WebSockets
  - Redis sorted sets for O(log n) rank queries
  - "Around me" view — see players ranked near you
  - Personal best tracking (only improves your rank on a new high score)

- **Comprehensive Testing**
  - Unit tests with mocked DB and Redis
  - Integration tests against real MySQL and Redis in Docker
  - Test coverage reports

## 🛠️ Tech Stack

- **Backend Framework:** FastAPI
- **Database:** MySQL (SQLAlchemy ORM)
- **Cache & Ranking:** Redis (sorted sets)
- **Authentication:** JWT + Bcrypt
- **Real-time Communication:** WebSockets
- **Image Storage:** Cloudinary
- **Task Scheduling:** APScheduler
- **Testing:** Pytest, pytest-mock
- **Containerization:** Docker & Docker Compose

## 📋 Prerequisites

- Docker & Docker Compose (everything else runs inside containers)

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd realtime-leaderboard-project

# Start all services
make dev

# Application runs on http://localhost:5000
```

## 📚 API Documentation

Once the server is running:
- **Swagger UI:** http://localhost:5000/docs

## 🔧 Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/leaderboard_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Email (Mailtrap)
MAIL_USERNAME=your-mailtrap-username
MAIL_PASSWORD=your-mailtrap-password
MAIL_FROM=noreply@yourapp.com

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## 📊 Database Schema

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full ERD and system diagrams.

## 🧪 Testing

```bash
# Run the full test suite
make test

# Run a single test by name
make test-one TARGET=test_successful_registration

# Stop and clean up test containers
make clean
```

### What's covered
- ✅ Authentication & authorization flows
- ✅ User lifecycle (register, verify, deactivate, reactivate, delete)
- ✅ Game CRUD operations
- ✅ Leaderboard submission and ranking
- ✅ WebSocket connection and disconnect handling
- ✅ Error handling and edge cases

## 🔐 Security Features

- **Password hashing:** Bcrypt with 12 rounds
- **Tokens:** JWT access tokens + refresh tokens (revoked on password reset)
- **Email verification:** Time-limited codes
- **Rate limiting:** Per-endpoint request throttling via fastapi-limiter
- **Admin guards:** Role-based access control on all management endpoints
- **Input validation:** Pydantic models with strict field-level validation

## 📈 Performance Decisions

- **Redis sorted sets** — rank queries and top-N lookups are O(log n) instead of a full SQL sort
- **Personal best tracking** — Redis is only updated when a user beats their previous high score, reducing unnecessary writes
- **Connection pooling** — SQLAlchemy pool with `pool_pre_ping` and `pool_recycle` to handle MySQL idle timeouts
- **Async Redis client** — separate async client for the WebSocket broadcast path to avoid blocking

## 🚦 Health Check

```bash
curl http://localhost:5000/health
```

Returns status of the app, MySQL connection, sync Redis client, and async Redis client independently.

## 🐳 Docker Commands

```bash
make dev        # Start all services in background
make test       # Run full test suite in Docker
make test-one TARGET=test_name  # Run a single test
make clean      # Stop and remove all containers and volumes
make build      # Rebuild images with no cache
```

## 📝 API Endpoints

### Authentication
- `POST /auth/register` — Register new user
- `POST /auth/login` — Login
- `POST /auth/refresh-token` — Refresh JWT token
- `GET /auth/verify-email?code=xxx` — Verify email
- `POST /auth/forgot-password` — Request password reset
- `POST /auth/reset-password` — Reset password with code
- `POST /auth/logout` — Revoke refresh token
- `POST /auth/resend-verification` — Resend verification email

### Users
- `GET /users/profile` — Get current user profile
- `GET /users/profile/{username}` — Get another user's public profile
- `PUT /users/profile` — Upload avatar
- `DELETE /users/profile/avatar` — Remove avatar
- `PUT /users/profile/deactivate` — Deactivate account
- `POST /users/reactivate-account` — Reactivate account
- `DELETE /users/profile` — Delete account permanently

### Games
- `POST /game/` — Create game (admin only)
- `GET /game/` — Get all games (admin only)
- `GET /game/list` — Get active games (public)
- `PATCH /game/activate/{game_name}` — Activate game (admin only)
- `PATCH /game/deactivate/{game_name}` — Deactivate game (admin only)
- `DELETE /game/{game_name}` — Delete game (admin only)

### Leaderboard
- `POST /leaderboard/submit-score` — Submit score
- `GET /leaderboard/get-leaderboard/{game_name}` — Get leaderboard
- `GET /leaderboard/get-leaderboard/{game_name}/user-rank` — Get your rank
- `GET /leaderboard/get-leaderboard/{game_name}/around-me` — Get players ranked near you
- `POST /leaderboard/refresh-leaderboard/{game_name}` — Rebuild leaderboard from DB (admin only)
- `POST /leaderboard/refresh-all-leaderboards` — Rebuild all leaderboards from DB (admin only)
- `POST /leaderboard/refresh-user-scores/{user_id}` — Rebuild a user's scores in Redis (admin only)

### WebSocket
- `WS /ws/{game_name}` — Connect for real-time leaderboard updates

## 👨‍💻 Author

Built as a side project to go deeper on Docker, Redis, and real-time systems.