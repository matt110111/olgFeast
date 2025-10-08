# olgFeast Docker Deployment Guide

This guide explains how to deploy and run the olgFeast application using Docker containers.

## 🚀 Quick Start

### Prerequisites
- Docker Engine (20.10+)
- Docker Compose (2.0+)

### Production Deployment

1. **Start the application:**
   ```bash
   ./docker-start.sh
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

3. **Stop the application:**
   ```bash
   ./docker-stop.sh
   ```

### Development Mode

For development with hot reloading:

```bash
./docker-dev.sh
```

## 📁 Docker Configuration

### Services

The application consists of 4 main services:

1. **Database (PostgreSQL)**
   - Port: 5432
   - Container: `olgfeast_db`
   - Data persistence: `postgres_data` volume

2. **Redis (WebSocket & Caching)**
   - Port: 6379
   - Container: `olgfeast_redis`
   - Data persistence: `redis_data` volume

3. **Backend (FastAPI)**
   - Port: 8000
   - Container: `olgfeast_backend`
   - Health check: `/health` endpoint

4. **Frontend (React + Nginx)**
   - Port: 3000
   - Container: `olgfeast_frontend`
   - Static files served via Nginx

### Configuration Files

- `docker-compose.yml` - Main production configuration
- `docker-compose.override.yml` - Development overrides
- `docker.env` - Environment variables template
- `.env` - Your environment configuration (auto-created from docker.env)

## 🔧 Manual Commands

### Build and Start
```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Development Mode
```bash
# Start with hot reloading
docker-compose -f docker-compose.yml -f docker-compose.override.yml up

# Start specific services
docker-compose up db redis backend
```

### Database Operations
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Access database shell
docker-compose exec db psql -U olgfeast -d olgfeast

# Backup database
docker-compose exec db pg_dump -U olgfeast olgfeast > backup.sql
```

### Maintenance
```bash
# Restart services
docker-compose restart

# Stop and remove containers
docker-compose down

# Remove volumes (⚠️ deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Full cleanup
docker-compose down -v --rmi all
```

## 🔒 Security Configuration

### Production Checklist

Before deploying to production:

1. **Update environment variables:**
   ```bash
   # Edit .env file
   nano .env
   
   # Change these values:
   SECRET_KEY=your-super-secure-random-key
   DEBUG=false
   ```

2. **Database security:**
   - Change default passwords in `docker-compose.yml`
   - Use strong passwords for `POSTGRES_PASSWORD` and Redis password

3. **Network security:**
   - Remove port mappings for database and Redis in production
   - Use reverse proxy (nginx/traefik) for SSL termination
   - Configure firewall rules

4. **SSL/TLS:**
   - Configure SSL certificates
   - Update nginx configuration for HTTPS
   - Set secure headers

## 📊 Monitoring & Logs

### Health Checks
All services include health checks:
- Database: `pg_isready`
- Redis: `redis-cli ping`
- Backend: HTTP `/health` endpoint
- Frontend: HTTP root endpoint

### Logging
- Logs are configured with rotation (10MB max, 3 files)
- View logs: `docker-compose logs -f [service_name]`
- Logs are stored in container filesystem

### Monitoring Commands
```bash
# Check all service health
docker-compose ps

# View resource usage
docker stats

# Check service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
docker-compose logs redis
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Check if ports are in use
   netstat -tulpn | grep :3000
   netstat -tulpn | grep :8000
   ```

2. **Permission issues:**
   ```bash
   # Fix script permissions
   chmod +x docker-start.sh docker-stop.sh docker-dev.sh
   ```

3. **Database connection issues:**
   ```bash
   # Check database logs
   docker-compose logs db
   
   # Reset database
   docker-compose down -v
   docker-compose up -d
   ```

4. **Build issues:**
   ```bash
   # Clean build
   docker-compose build --no-cache
   
   # Remove old images
   docker image prune -a
   ```

### Performance Optimization

1. **Resource limits:**
   Add to `docker-compose.yml`:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 512M
             cpus: '0.5'
   ```

2. **Database optimization:**
   - Configure PostgreSQL settings in environment
   - Use connection pooling
   - Monitor query performance

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale backend services
docker-compose up -d --scale backend=3

# Use load balancer (nginx/traefik)
# Configure session affinity for WebSocket connections
```

### Production Deployment
For production deployment:
1. Use Docker Swarm or Kubernetes
2. Configure persistent volumes
3. Set up monitoring (Prometheus/Grafana)
4. Configure log aggregation
5. Set up backup strategies

## 🔄 Updates

### Application Updates
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations if needed
docker-compose exec backend alembic upgrade head
```

### Zero-downtime Updates
For zero-downtime updates:
1. Use blue-green deployment
2. Configure health checks
3. Use rolling updates with Docker Swarm
4. Set up proper load balancing

## 📞 Support

For issues and questions:
1. Check the logs: `docker-compose logs -f`
2. Verify service health: `docker-compose ps`
3. Check configuration files
4. Review this documentation

## 🎯 Next Steps

After successful deployment:
1. Configure monitoring and alerting
2. Set up automated backups
3. Implement CI/CD pipeline
4. Configure SSL certificates
5. Set up log aggregation
6. Implement security scanning
