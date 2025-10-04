# olgFeast Deployment Guide

This guide covers deployment of the olgFeast restaurant management system from development to production.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React SPA     │    │   FastAPI       │    │   PostgreSQL    │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Database)    │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     Redis       │
                       │   (WebSocket)   │
                       │   Port: 6379    │
                       └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.13+ (for development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd olgFeast
cp env.example .env
# Edit .env with your configuration
```

### 2. Deploy with Docker

```bash
# Make deployment script executable
chmod +x deploy.sh

# Deploy to development
./deploy.sh development

# Deploy to production
./deploy.sh production
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/admin

## Development Setup

### Backend (FastAPI)

```bash
cd fastapi_app

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python start_dev.py
```

### Frontend (React)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## Production Deployment

### Docker Compose

The application uses Docker Compose for orchestration:

```yaml
# docker-compose.yml
services:
  - PostgreSQL (Database)
  - Redis (WebSocket channels)
  - FastAPI (Backend API)
  - React (Frontend SPA)
```

### Environment Configuration

Create `.env` file with production settings:

```env
# Database
DATABASE_URL=postgresql://user:password@db:5432/olgfeast

# Redis
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your-super-secret-production-key
DEBUG=false

# CORS
ALLOWED_HOSTS=["yourdomain.com", "api.yourdomain.com"]
```

### SSL/HTTPS Setup

For production, configure SSL certificates:

```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://frontend:80;
    }
    
    location /api/ {
        proxy_pass http://backend:8000;
    }
}
```

## Testing

### Backend Tests

```bash
cd fastapi_app

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run performance tests
pytest tests/test_performance.py -v -s
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run linting
npm run lint
```

### Integration Tests

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
docker-compose exec test-backend pytest tests/integration/ -v

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

## Monitoring and Logging

### Health Checks

All services include health check endpoints:

- **Backend**: `GET /health`
- **Frontend**: `GET /`
- **Database**: PostgreSQL health check
- **Redis**: Redis ping

### Logging

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Performance Monitoring

The application includes performance tests that monitor:

- API response times
- Concurrent request handling
- Memory usage
- Database query performance

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
  
  frontend:
    deploy:
      replicas: 2
```

### Load Balancing

```nginx
# nginx.conf
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

## Database Management

### Migrations

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

### Backup and Restore

```bash
# Backup database
docker-compose exec db pg_dump -U olgfeast olgfeast > backup.sql

# Restore database
docker-compose exec -T db psql -U olgfeast olgfeast < backup.sql
```

## Security

### Environment Variables

Never commit sensitive data:

```bash
# .env (never commit)
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@host:port/db
REDIS_URL=redis://password@host:port
```

### HTTPS Configuration

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    # SSL configuration
}
```

### CORS Configuration

```python
# FastAPI CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Change ports in docker-compose.yml
2. **Database connection**: Check DATABASE_URL in .env
3. **Redis connection**: Check REDIS_URL in .env
4. **CORS errors**: Update ALLOWED_HOSTS in .env

### Debug Mode

```bash
# Enable debug mode
DEBUG=true docker-compose up

# View detailed logs
docker-compose logs -f --tail=100
```

### Performance Issues

```bash
# Run performance tests
docker-compose exec backend pytest tests/test_performance.py -v -s

# Monitor resource usage
docker stats

# Check database performance
docker-compose exec db psql -U olgfeast olgfeast -c "EXPLAIN ANALYZE SELECT * FROM orders;"
```

## CI/CD Pipeline

The application includes a GitHub Actions CI/CD pipeline:

1. **Code Quality**: Linting, formatting, type checking
2. **Testing**: Unit tests, integration tests, performance tests
3. **Security**: Vulnerability scanning
4. **Deployment**: Automated deployment to staging/production

### Pipeline Stages

```yaml
# .github/workflows/ci.yml
jobs:
  - backend-tests
  - frontend-tests
  - integration-tests
  - security-scan
  - deploy-staging (develop branch)
  - deploy-production (main branch)
```

## Maintenance

### Updates

```bash
# Update dependencies
cd fastapi_app && pip install -r requirements.txt --upgrade
cd frontend && npm update

# Rebuild containers
docker-compose up -d --build
```

### Cleanup

```bash
# Remove unused containers
docker-compose down --rmi all --volumes --remove-orphans

# Clean Docker cache
docker system prune -a
```

## Support

For issues and questions:

1. Check the logs: `docker-compose logs -f`
2. Run tests: `pytest tests/ -v`
3. Check performance: `pytest tests/test_performance.py -v -s`
4. Review documentation: API docs at `/docs`

## Performance Benchmarks

Based on performance tests:

- **API Response Time**: < 100ms average
- **Concurrent Requests**: 50 requests in < 250ms
- **Cart Operations**: < 50ms each
- **Order Creation**: < 100ms
- **Authentication**: < 20ms
- **Memory Usage**: < 50MB increase for 100 requests

## Migration from Django

This FastAPI version provides significant improvements:

- **Performance**: 3-5x faster API responses
- **Real-time**: Native WebSocket support
- **Type Safety**: Full TypeScript/type hint coverage
- **Modern Stack**: React SPA with modern tooling
- **Scalability**: Better horizontal scaling capabilities
- **Developer Experience**: Hot reload, automatic API docs
