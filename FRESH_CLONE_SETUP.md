# 🚀 Fresh Clone Setup Guide

This guide will help you get OlgFeast running on a fresh clone of the repository.

## Prerequisites

Before running the setup script, ensure you have:

1. **Docker & Docker Compose** installed and running
2. **Git** installed
3. **Terminal/Command Line** access

### Quick Prerequisites Check

```bash
# Check if Docker is running
docker --version
docker-compose --version
docker info

# If Docker is not running, start it:
# - On Linux: sudo systemctl start docker
# - On macOS: Start Docker Desktop
# - On Windows: Start Docker Desktop
```

## One-Command Setup

Once you have the prerequisites, simply run:

```bash
# Make the script executable (if needed)
chmod +x first_time_setup.sh

# Run the automated setup
./first_time_setup.sh
```

## What the Setup Script Does

The `first_time_setup.sh` script will automatically:

1. ✅ **Check Prerequisites** - Verify Docker and docker-compose are available
2. ✅ **Generate Environment File** - Create `docker.env` with secure random passwords
3. ✅ **Start Database Services** - Launch PostgreSQL and Redis containers
4. ✅ **Initialize Database** - Create tables and seed with sample data
5. ✅ **Generate Credentials** - Create admin and customer accounts with secure passwords
6. ✅ **Start Application** - Launch backend and frontend services
7. ✅ **Health Checks** - Verify all services are running properly

## After Setup

Once the script completes successfully, you'll have:

### 🌐 Access URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 🔐 Login Credentials
The script generates secure credentials and saves them to `deployment_credentials.txt`. 

**Important**: Check this file for your login credentials and delete it after noting them down!

### 🎯 Default Users
- **Admin User**: Full access to admin panel, menu management, and order oversight
- **Customer User**: Can browse menu, place orders, and view order history

## Troubleshooting

### Common Issues

**Docker not running**:
```bash
# Start Docker service
sudo systemctl start docker  # Linux
# OR start Docker Desktop on macOS/Windows
```

**Port conflicts**:
- Ensure ports 3000, 8000, 5432, and 6379 are not in use
- Stop other applications using these ports

**Permission issues**:
```bash
# Make script executable
chmod +x first_time_setup.sh

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
# Log out and back in
```

### Cleanup and Restart

If you need to start over:

```bash
# Stop all services and remove containers/volumes
./first_time_setup.sh cleanup

# Restart services
./first_time_setup.sh restart

# View logs
./first_time_setup.sh logs

# Check service status
./first_time_setup.sh status
```

## Next Steps

1. **Access the application** at http://localhost:3000
2. **Login with admin credentials** to access the admin panel
3. **Change default passwords** for security
4. **Explore the features**:
   - Menu management
   - Order processing
   - Kitchen display
   - User management

## Security Notes

⚠️ **Important Security Reminders**:
- Change default passwords immediately after first login
- Keep `docker.env` file secure and never commit it to version control
- Delete `deployment_credentials.txt` after noting credentials
- Set up proper firewall rules for production deployment
- Use HTTPS in production environments

---

**Need Help?** Check the main [README.md](README.md) for more detailed information about the application features and development setup.
