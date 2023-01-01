# SoleCraft API 👟

A production-ready backend API for a customizable shoes selling platform built with FastAPI, PostgreSQL, and clean architecture principles.

## 🚀 Features

### 🧱 Architecture
- **Clean Architecture** with proper separation of concerns
- **Domain-Driven Design** with distinct business domains
- **Repository Pattern** for data access abstraction
- **Dependency Injection** for loose coupling
- **SOLID Principles** implementation

### 🛍️ Business Features
- **Multi-tenant Support** - Both guest and registered users
- **Product Customization** - Text, image, and select-based customizations
- **Advanced Inventory** - Variant-based stock management
- **Shopping Cart** - Persistent cart with customizations
- **Order Management** - Complete order lifecycle
- **Review System** - Product reviews and ratings
- **Discount Codes** - Flexible coupon system

### 🔐 Security & Auth
- **JWT Authentication** for registered users
- **Guest Checkout** flow
- **Rate Limiting** middleware
- **Input Validation** with Pydantic
- **Security Headers** and CORS configuration

### ⚡ Performance & Scalability
- **Async/Await** throughout the application
- **Database Connection Pooling**
- **Redis Caching** support
- **Celery Task Queue** for background jobs
- **Structured Logging** with correlation IDs
- **Health Checks** and monitoring

## 🏗️ Architecture Overview

```
solecraft-api/
├── api/                    # FastAPI routers (REST endpoints)
├── controllers/            # Input validation and output formatting
├── services/              # Core business logic
├── repositories/          # Data access layer
├── interfaces/            # Abstract interfaces (Dependency Inversion)
├── models/
│   ├── orm/              # SQLAlchemy models
│   └── schemas/          # Pydantic models
├── middleware/            # Custom middlewares
├── infrastructure/        # DB setup, email, logger, broker
├── workers/              # Celery workers for async tasks
├── core/                 # Global config, constants, DI container
├── tests/                # Unit and integration tests
├── migrations/           # Alembic database migrations
├── main.py              # FastAPI app entry point
├── Dockerfile           # Production Docker image
├── docker-compose.yml   # Multi-service orchestration
└── alembic.ini         # Database migration configuration
```

## 📦 Database Schema

### Core Entities

#### User Domain
- **Users** - Both registered and guest users
- **Addresses** - Multiple addresses per user

#### Product Domain
- **Categories** - Hierarchical product categories
- **Products** - Base product information
- **ProductVariants** - Color, size, material variations
- **ProductCustomizations** - Customization options

#### Commerce Domain
- **Cart** - Shopping cart with items
- **CartItems** - Products with customizations in cart
- **Orders** - Complete order information
- **OrderItems** - Order line items with customizations

#### Engagement Domain
- **Reviews** - Product reviews and ratings
- **DiscountCodes** - Coupon and discount system

## 🛠️ Technology Stack

### Core Framework
- **FastAPI** - Modern async web framework
- **Python 3.11+** - Latest Python features
- **Pydantic v2** - Data validation and serialization
- **SQLAlchemy 2.0** - Modern async ORM

### Database & Storage
- **PostgreSQL 15** - Primary database
- **Redis 7** - Caching and session storage
- **Alembic** - Database migrations

### Background Tasks
- **Celery** - Distributed task queue
- **RabbitMQ** - Message broker
- **Flower** - Task monitoring

### DevOps & Deployment
- **Docker** - Containerization
- **Docker Compose** - Multi-service orchestration
- **Gunicorn** - WSGI server for production
- **Nginx** - Reverse proxy (optional)

### Development Tools
- **Black** - Code formatting
- **isort** - Import sorting
- **Flake8** - Linting
- **MyPy** - Type checking
- **Pytest** - Testing framework

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (if running locally)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd solecraft-api
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Run with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Database Setup
```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create initial data (optional)
docker-compose exec api python scripts/seed_data.py
```

## 🔧 Local Development

### 1. Setup Virtual Environment
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

### 2. Database Setup
```bash
# Start only database services
docker-compose up -d postgres redis rabbitmq

# Run migrations
alembic upgrade head
```

### 3. Run the Application
```bash
# Development server with auto-reload
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run Celery Worker (separate terminal)
```bash
celery -A workers.celery_app worker --loglevel=info
```

### 5. Run Celery Beat (separate terminal)
```bash
celery -A workers.celery_app beat --loglevel=info
```

## 📡 API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

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