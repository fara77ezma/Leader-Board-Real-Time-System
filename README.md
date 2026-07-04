# Real-time Leaderboard System

A modern, scalable backend system for managing real-time leaderboards with game management, user authentication, and WebSocket support. Built with FastAPI, Redis, and MySQL.

## 🎯 Features

- **User Authentication & Authorization**
  - JWT-based authentication with refresh tokens
  - Email verification with expiring verification codes
  - Password reset functionality
  - Admin role management

- **Game Management**
  - Create, read, update, delete games
  - Activate/deactivate games
  - Public game listing endpoint

- **Real-time Leaderboard**
  - Real-time score updates via WebSockets
  - Efficient score tracking with Redis caching
  - Automatic ranking calculations
  - Sorted leaderboard queries

- **Comprehensive Testing**
  - Unit and integration tests
  - Test coverage reports
  - Docker-based test environment

## 🛠️ Tech Stack

- **Backend Framework:** FastAPI
- **Database:** MySQL/PostgreSQL (SQLAlchemy ORM)
- **Cache & Real-time:** Redis
- **Authentication:** JWT, Bcrypt
- **Real-time Communication:** WebSockets
- **Task Scheduling:** APScheduler
- **Testing:** Pytest, Docker Compose
- **Containerization:** Docker

## 📋 Prerequisites

- Python 3.9+
- Docker & Docker Compose
- MySQL or PostgreSQL
- Redis

## 🚀 Installation & Setup

### Using Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd realtime-leaderboard-project

# Run with Docker
docker-compose up

# Application runs on http://localhost:8000
```
## 📚 API Documentation

Once the server is running, access the interactive API documentation:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🔧 Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/leaderboard_db

# Redis
REDIS_URL=redis://localhost:6379

# Email Configuration
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=1
JWT_REFRESH_EXPIRATION_DAYS=7

# Cloudinary (for image uploads)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Verification Code Expiry
EMAIL_VERIFICATION_EXPIRY_MINUTES=15
PASSWORD_RESET_EXPIRY_MINUTES=30
```
## 📊 Database Schema

See the ERD diagram in [ARCHITECTURE.md](./ARCHITECTURE.md) for visual representation.

### Core Tables

**users**
- Unique user identification with `user_code`
- Email verification workflow
- Password reset tokens
- Admin role support
- Avatar storage with Cloudinary

**game**
- Active/inactive game status
- Game descriptions
- Timestamps for auditing

**leaderboard**
- Score tracking per user per game
- Foreign keys to users and games
- Automatic ranking via queries

**refresh_tokens**
- Token-based session management
- Revocation support
- Expiration tracking

## 🧪 Testing

Run the complete test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test class
pytest tests/test_auth.py::TestAuthEndpoint

# Run with verbose output
pytest -v
```

### Test Coverage
- ✅ Authentication & authorization
- ✅ User lifecycle management
- ✅ Game CRUD operations
- ✅ Real-time leaderboard updates
- ✅ WebSocket connections
- ✅ Error handling & edge cases

## 🔐 Security Features

- **Password Security:** Bcrypt hashing with salt
- **Authentication:** JWT with expiring tokens and refresh mechanism
- **Email Verification:** Time-limited verification codes
- **Rate Limiting:** Per-endpoint request throttling
- **Admin Verification:** Role-based access control
- **Input Validation:** Pydantic models with strict validation

## 📈 Performance Features

- **Redis Caching:** Fast leaderboard queries
- **Connection Pooling:** Efficient database connections
- **Async Operations:** Non-blocking I/O for WebSockets
- **Task Scheduling:** Automatic cleanup of expired tokens
- **Pagination:** Efficient large dataset handling

## 🚦 Health Check

Monitor system health:

```bash
curl http://localhost:8000/health
```

Returns status of:
- Application
- Database connection
- Redis (sync client)
- Redis (async client)

## 🐳 Docker Commands

```bash
# Build images
docker-compose build

# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Run tests in Docker
docker-compose -f docker-compose.test.yml up

# Stop services
docker-compose down

# Remove all data and volumes
docker-compose down -v
```

## 📝 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh-token` - Refresh JWT token
- `GET /auth/verify-email` - Verify email with code
- `POST /auth/request-password-reset` - Request password reset
- `POST /auth/reset-password` - Reset password with code

### Users
- `GET /users/me` - Get current user profile
- `GET /users/{username}` - Get user by username
- `PATCH /users/{username}/avatar` - Upload avatar
- `GET /users/` - List all users (admin only)

### Games
- `POST /game/` - Create game (admin only)
- `GET /game/` - Get all games (admin only)
- `GET /game/list` - Get active games (public)
- `PATCH /game/activate/{name}` - Activate game
- `PATCH /game/deactivate/{name}` - Deactivate game
- `DELETE /game/{name}` - Delete game

### Leaderboard
- `POST /leaderboard/score` - Submit score
- `GET /leaderboard/{game_name}` - Get game leaderboard
- `GET /leaderboard/{game_name}/{username}` - Get user rank

### WebSocket
- `WS /ws/{game_name}` - Real-time leaderboard updates

## 👨‍💻 Author

Built as a learning project to master Docker, Redis, and Python backend development.