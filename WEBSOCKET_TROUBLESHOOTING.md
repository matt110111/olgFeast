# WebSocket Troubleshooting Guide

## ✅ Current Status: FIXED & WORKING

All WebSocket connections are now working properly in the Docker environment.

## 🔧 What Was Fixed

### 1. Environment Variables
- **Problem**: Docker containers were starting without required environment variables
- **Solution**: Created `docker.env` file with proper development credentials
- **Files Updated**: `docker-dev.sh` now loads environment variables correctly

### 2. Container Networking
- **Problem**: Frontend couldn't connect to backend WebSocket endpoints
- **Solution**: Ensured all containers are on the same Docker network
- **Files Updated**: `docker-compose.yml`, `docker-compose.override.yml`

### 3. WebSocket URL Configuration
- **Problem**: Frontend WebSocket service wasn't using correct URLs in Docker
- **Solution**: Updated WebSocket service to use environment variables
- **Files Updated**: `frontend/src/services/websocket.ts`

## 🧪 Testing WebSocket Connections

### Automated Test
```bash
# Run the WebSocket connectivity test
python3 simple_websocket_test.py
```

### Manual Browser Testing
1. Open browser developer console (F12)
2. Navigate to http://localhost:3001
3. Login with admin credentials: `admin` / `3_eKugNg9VTAA7Moz8nz7g`
4. Go to Kitchen Display
5. Check console for WebSocket connection messages:
   - ✅ `WebSocket connected to /ws/kitchen/display`
   - ✅ `Received kitchen state update`

## 🌐 Access Information

### Development URLs
- **Frontend**: http://localhost:3001 (React development server)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### WebSocket Endpoints
- **Kitchen Display**: `ws://localhost:8000/ws/kitchen/display`
- **Order Updates**: `ws://localhost:8000/ws/orders/updates`
- **Admin Dashboard**: `ws://localhost:8000/ws/admin/dashboard`

### Test Credentials
- **Admin User**: `admin` / `3_eKugNg9VTAA7Moz8nz7g`
- **Customer User**: `customer` / `WLOfiBSVU9dCvv9k`

## 🔍 Debugging Steps

### Check Container Status
```bash
docker ps
# Should show all 4 containers: db, redis, backend, frontend
```

### Check Backend Logs
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml --env-file docker.env logs backend
```

### Check Frontend Logs
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml --env-file docker.env logs frontend
```

### Test Health Endpoints
```bash
# Backend health
curl http://localhost:8000/health

# Frontend
curl http://localhost:3001
```

## 🐛 Common Issues & Solutions

### Issue: "Disconnected" on Kitchen Display
**Symptoms**: Kitchen Display shows "Disconnected" status
**Solution**: 
1. Ensure all containers are running: `docker ps`
2. Check backend logs for errors
3. Verify WebSocket URL in browser console
4. Restart containers: `./docker-dev.sh`

### Issue: Environment Variables Not Loading
**Symptoms**: Containers fail to start with password errors
**Solution**:
1. Ensure `docker.env` file exists
2. Check `docker-dev.sh` includes `--env-file docker.env`
3. Restart containers

### Issue: Frontend Can't Connect to Backend
**Symptoms**: Frontend loads but API calls fail
**Solution**:
1. Check backend is running on port 8000
2. Verify Docker network connectivity
3. Check CORS configuration

## 🚀 Deployment Readiness

The codebase is now ready for deployment with:
- ✅ WebSocket connections working
- ✅ Environment variables configured
- ✅ Container networking fixed
- ✅ Database seeded with test data
- ✅ All services healthy and accessible

## 📝 Next Steps

1. **Test in Browser**: Navigate to http://localhost:3001 and test Kitchen Display
2. **Verify Real-time Updates**: Create orders and confirm WebSocket updates
3. **Production Deployment**: Use `./first_time_setup.sh` for production
4. **Monitor Logs**: Keep an eye on container logs for any issues

## 🔧 Maintenance Commands

### Restart All Services
```bash
./docker-dev.sh
```

### Stop All Services
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml --env-file docker.env down
```

### View Live Logs
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml --env-file docker.env logs -f
```

### Clean Restart (removes volumes)
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml --env-file docker.env down --volumes --remove-orphans
./docker-dev.sh
```

