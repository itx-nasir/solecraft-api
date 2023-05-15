# SoleCraft API 👟

A production-ready backend API for a customizable shoes selling platform built with FastAPI, PostgreSQL, and clean architecture principles.

## 🚀 Features

### 🧱 Architecture
- **Layered Architecture** with proper separation of concerns
- **Service Layer** for core business logic
- **Pydantic** for robust data validation
- **SOLID Principles** implementation

### 🛍️ Business Features
- **Guest and Registered Users**
- **Product Management**
- **Shopping Cart**
- **Order Management**
- **Review System**

### 🔐 Security & Auth
- **JWT Authentication** for registered users
- **Admin and User Roles** via a simple `is_admin` flag
- **Rate Limiting** middleware
- **Input Validation** with Pydantic
- **CORS** configuration

### ⚡ Performance & Scalability
- **Async/Await** throughout the application
- **Database Connection Pooling**
- **FastAPI BackgroundTasks** for asynchronous operations
- **APScheduler** for scheduled jobs
- **Structured Logging**
- **Health Checks** and monitoring

## 🏗️ Architecture Overview

The architecture is simplified for ease of development and deployment, focusing on a clear separation of concerns without unnecessary layers for an MVP.

```
solecraft-api/
├── api/                    # FastAPI routers (REST endpoints)
├── services/               # Core business logic and database interaction
├── models/
│   ├── orm/                # SQLAlchemy models (data structure)
│   └── schemas/            # Pydantic models (API data shapes)
├── middleware/             # Custom middlewares (e.g., auth)
├── core/                   # Global config, scheduler, and database setup
├── tests/                  # Unit and integration tests
├── migrations/             # Alembic database migrations
├── main.py                 # FastAPI app entry point
├── Dockerfile              # Production Docker image
├── docker-compose.yml      # Local development setup
└── requirements.txt        # Python dependencies
```

## 🛠️ Technology Stack

### Core Framework
- **FastAPI** - Modern async web framework
- **Python 3.11+** - Latest Python features
- **Pydantic v2** - Data validation and serialization
- **SQLAlchemy 2.0** - Modern async ORM

### Database & Storage
- **PostgreSQL 15** - Primary database
- **Alembic** - Database migrations

### Background Tasks
- **FastAPI BackgroundTasks** - For tasks like sending emails
- **APScheduler** - For scheduled cleanup jobs

### DevOps & Deployment
- **Docker** - Containerization
- **Docker Compose** - Local development orchestration

### Development Tools
- **Black** - Code formatting
- **isort** - Import sorting
- **Flake8** - Linting
- **MyPy** - Type checking
- **Pytest** - Testing framework

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose

### 1. Clone the Repository
```bash
git clone <repository-url>
cd solecraft-api
```

### 2. Run with Docker Compose
This is the fastest way to get started. It will build the API image and start a PostgreSQL database container.

```bash
# Start all services in the background
docker-compose up -d --build

# View logs for the API
docker-compose logs -f api

# Stop services
docker-compose down
```
The API will be available at `http://localhost:8000`.

### 3. Database Migrations
Once the containers are running, apply the database migrations.

```bash
# Run migrations
docker-compose exec api alembic upgrade head
```
This command only needs to be run once initially and then again anytime there are new migrations.

## 🔧 Local Development (Without Docker for the API)

If you prefer to run the Python application directly on your machine.

### 1. Start Database
```bash
# Start only the postgres database service
docker-compose up -d postgres
```

### 2. Setup Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
The application uses Pydantic settings and reads from environment variables. You can use a `.env` file for local development.
```bash
# The application will work with default settings pointing to the local Docker database.
# You can create a .env file to override settings if needed.
# Example:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/solecraft_db
```

### 4. Run Migrations
```bash
# Ensure your .env file is configured or variables are exported
alembic upgrade head
```

### 5. Run the Application
```bash
# The app will start with auto-reload
uvicorn main:app --reload
```

## 📡 API Documentation

Once the application is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/guest` - Create guest user
- `POST /auth/refresh` - Refresh JWT token

#### Products
- `GET /products` - List products with search and filters
- `GET /products/{slug}` - Get product details
- `GET /categories` - List categories
- `GET /products/{id}/reviews` - Product reviews

#### Cart & Orders
- `GET /cart` - Get user's cart
- `POST /cart/items` - Add item to cart
- `PUT /cart/items/{id}` - Update cart item
- `DELETE /cart/items/{id}` - Remove cart item
- `POST /checkout` - Create order from cart
- `GET /orders` - List user orders
- `GET /orders/{id}` - Get order details

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=./ --cov-report=html

# Run specific test file
pytest tests/test_users.py

# Run with specific marker
pytest -m "unit"
```

### Test Categories
- **Unit Tests** - Individual component testing
- **Integration Tests** - Database and service integration
- **End-to-End Tests** - Complete API workflow testing

## 🔄 Database Migrations

### Create New Migration
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user table"

# Create empty migration
alembic revision -m "Custom migration"
```

### Apply Migrations
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade one revision
alembic downgrade -1
```

### Migration History
```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic show <revision_id>
```

## 📊 Monitoring & Logging

### Application Monitoring
- **Health Check**: http://localhost:8000/health
- **Application Logs**: Structured JSON logging
- **Sentry Integration**: Error tracking (configure SENTRY_DSN)

### Celery Monitoring
- **Flower Dashboard**: http://localhost:5555
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

### Database Monitoring
- **Connection via psql**: `docker-compose exec postgres psql -U postgres -d solecraft_db`

## 🚀 Production Deployment

### Environment Variables
```bash
# Required production settings
DEBUG=false
ENVIRONMENT=production
JWT_SECRET_KEY=<secure-random-key>
DATABASE_URL=<production-db-url>
REDIS_URL=<production-redis-url>
SENTRY_DSN=<sentry-project-dsn>
```

### Docker Production
```bash
# Build production image
docker build -t solecraft-api:latest .

# Run with production environment
docker run -d \
  --name solecraft-api \
  -p 8000:8000 \
  --env-file .env.production \
  solecraft-api:latest
```

### Security Checklist
- [ ] Change default JWT secret key
- [ ] Use strong database passwords
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure firewall rules
- [ ] Set up regular backups
- [ ] Enable monitoring and alerting
- [ ] Review CORS settings
- [ ] Implement rate limiting in production

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints
- Write comprehensive docstrings
- Maintain test coverage above 80%
- Use meaningful commit messages

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 📋 API Features Overview

### ✅ Implemented Features
- [x] User authentication (JWT + Guest)
- [x] Product catalog with variants
- [x] Product customization system
- [x] Shopping cart functionality
- [x] Order management
- [x] Review and rating system
- [x] Discount code system
- [x] Database migrations
- [x] Background task processing
- [x] Comprehensive API documentation
- [x] Docker containerization
- [x] Health checks and monitoring
- [x] Structured logging
- [x] Input validation and error handling

### 🚧 Future Enhancements
- [ ] Payment processing integration (Stripe)
- [ ] Email notifications
- [ ] File upload handling
- [ ] Advanced search with Elasticsearch
- [ ] Inventory management alerts
- [ ] Admin dashboard API
- [ ] Multi-language support
- [ ] Analytics and reporting
- [ ] Wishlist functionality
- [ ] Product recommendations

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For questions, issues, or contributions:

1. Check the [Issues](../../issues) page
2. Review the [API Documentation](http://localhost:8000/docs)
3. Create a new issue with detailed information

---

**Built with ❤️ for modern e-commerce platforms**