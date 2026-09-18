# 🚀 OlgFeast Setup Guide for New Device

## Prerequisites

### 1. Install Docker & Docker Compose
```bash
# On Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in to apply docker group changes
```

### 2. Clone the Repository
```bash
git clone <your-repo-url> olgFeast
cd olgFeast
```

## Quick Setup (Recommended)

### Option 1: Automated Setup Script
```bash
# Make the script executable
chmod +x first_time_setup.sh

# Run the automated setup
./first_time_setup.sh
```

This script will:
- ✅ Check Docker installation
- ✅ Create production environment file
- ✅ Start database and Redis services
- ✅ Initialize database with demo data
- ✅ Start the full application

### Option 2: Manual Setup

#### Step 1: Create Environment File
```bash
# Copy the example environment file
cp env.example docker.env

# Edit the file with your preferred values (optional)
nano docker.env
```

#### Step 2: Start the Application
```bash
# Production mode (recommended)
./docker-start.sh

# OR manually with docker-compose
docker-compose -f docker-compose.yml --env-file docker.env up -d
```

#### Step 3: Initialize Database (if needed)
```bash
# Wait for services to start, then seed the database
sleep 30
docker-compose -f docker-compose.yml --env-file docker.env exec backend python setup_database.py
```

## Access Your Application

Once everything is running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Demo Credentials

The setup script creates demo users:
- **Admin**: `admin` / `[generated-password]`
- **Customer**: `customer` / `[generated-password]`

Check the terminal output during setup for the actual passwords.

## Development Mode

For development with hot-reloading:

```bash
# Start development environment
./docker-dev.sh

# The frontend will be available at http://localhost:3001
# Backend remains at http://localhost:8000
```

## Troubleshooting

### Check Service Status
```bash
docker-compose -f docker-compose.yml --env-file docker.env ps
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.yml --env-file docker.env logs -f

# Specific service
docker-compose -f docker-compose.yml --env-file docker.env logs -f backend
```

### Reset Everything
```bash
# Stop and remove all containers, networks, and volumes
./docker-stop.sh

# OR manually
docker-compose -f docker-compose.yml --env-file docker.env down -v
```

### Common Issues

1. **Port conflicts**: Make sure ports 3000, 8000, 5432, and 6379 are available
2. **Permission issues**: Ensure your user is in the docker group
3. **Container name conflicts**: Run `docker system prune -f` to clean up

## File Structure

```
olgFeast/
├── docker-compose.yml          # Production configuration
├── docker-compose.override.yml # Development overrides
├── docker.env                  # Environment variables (created by setup)
├── first_time_setup.sh         # Automated setup script
├── docker-start.sh             # Start production
├── docker-dev.sh               # Start development
├── docker-stop.sh              # Stop all services
├── fastapi_app/                # Backend application
└── frontend/                   # React frontend
```

## Production Deployment

For production deployment:

1. **Update environment variables** in `docker.env`:
   - Change `SECRET_KEY` to a secure random string
   - Update `POSTGRES_PASSWORD` and `REDIS_PASSWORD`
   - Set appropriate `BACKEND_CORS_ORIGINS`

2. **Use production scripts**:
   ```bash
   ./docker-start.sh  # Start in background
   ./docker-stop.sh   # Stop services
   ```

3. **Monitor logs**:
   ```bash
   docker-compose -f docker-compose.yml --env-file docker.env logs -f
   ```

## Need Help?

Check the logs first:
```bash
docker-compose -f docker-compose.yml --env-file docker.env logs
```

The application includes:
- ✅ FastAPI backend with PostgreSQL
- ✅ React frontend with dark/light theme
- ✅ Real-time WebSocket updates
- ✅ Admin dashboard and kitchen display
- ✅ Dockerized for easy deployment
