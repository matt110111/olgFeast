# OlgFeast - Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying OlgFeast to production with a clean database setup and secure first-time configuration.

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Docker**: Version 20.10.0 or higher
- **Docker Compose**: Version 2.0.0 or higher
- **RAM**: Minimum 2GB, recommended 4GB+
- **Disk Space**: Minimum 5GB free space
- **Network**: Internet connection for pulling Docker images

### Software Installation

#### Docker Installation (Ubuntu/Debian)
```bash
# Update package index
sudo apt-get update

# Install required packages
sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Docker Installation (macOS)
```bash
# Install using Homebrew
brew install docker docker-compose

# Or download Docker Desktop from https://www.docker.com/products/docker-desktop
```

#### Docker Installation (Windows)
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Install and restart your computer
3. Enable WSL2 integration if using WSL

## Deployment Steps

### 1. Download OlgFeast

```bash
# Clone the repository
git clone <repository-url>
cd olgFeast

# Or download and extract the zip file
wget <download-url>
unzip olgFeast.zip
cd olgFeast
```

### 2. First-Time Setup

Run the automated setup script:

```bash
# Make the script executable
chmod +x first_time_setup.sh

# Run the setup
./first_time_setup.sh
```

The setup script will:
- ✅ Check Docker installation
- ✅ Create secure environment variables
- ✅ Initialize the database with schema
- ✅ Create admin and customer accounts with random passwords
- ✅ Start all services
- ✅ Perform health checks

### 3. Access the Application

After successful setup:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Initial Login

Check the generated credentials:

```bash
cat deployment_credentials.txt
```

**Default Accounts:**
- **Admin**: `admin` / `<generated-password>`
- **Customer**: `customer` / `<generated-password>`

⚠️ **IMPORTANT**: Change these passwords immediately after first login!

## Configuration

### Environment Variables

The setup creates a `docker.env` file with the following variables:

```bash
# Database Configuration
POSTGRES_DB=olgfeast
POSTGRES_USER=olgfeast
POSTGRES_PASSWORD=<generated-secure-password>

# Redis Configuration
REDIS_PASSWORD=<generated-secure-password>

# Application Configuration
SECRET_KEY=<generated-secure-key>
DEBUG=false
ENVIRONMENT=production
```

### Customizing Configuration

To modify the configuration:

1. Edit `docker.env` file
2. Restart services: `./first_time_setup.sh restart`

### Domain Configuration

For production with a custom domain:

1. Update `BACKEND_CORS_ORIGINS` in `docker.env`
2. Configure reverse proxy (nginx recommended)
3. Set up SSL certificates

## Management Commands

### Service Management

```bash
# Check service status
./first_time_setup.sh status

# View logs
./first_time_setup.sh logs

# Restart services
./first_time_setup.sh restart

# Stop services
docker-compose -f docker-compose.yml --env-file docker.env down

# Start services
docker-compose -f docker-compose.yml --env-file docker.env up -d
```

### Database Management

```bash
# Access database
docker-compose -f docker-compose.yml --env-file docker.env exec db psql -U olgfeast -d olgfeast

# Backup database
docker-compose -f docker-compose.yml --env-file docker.env exec db pg_dump -U olgfeast olgfeast > backup.sql

# Restore database
docker-compose -f docker-compose.yml --env-file docker.env exec -T db psql -U olgfeast -d olgfeast < backup.sql

# Reset database (WARNING: This will delete all data)
docker-compose -f docker-compose.yml --env-file docker.env exec backend python setup_database.py cleanup
```

### User Management

```bash
# Create new admin user (via API)
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newadmin",
    "email": "newadmin@example.com",
    "password": "securepassword123",
    "is_staff": true
  }'

# Create new customer user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newcustomer",
    "email": "newcustomer@example.com",
    "password": "securepassword123",
    "is_staff": false
  }'
```

## Security Considerations

### Production Security Checklist

- [ ] Change default passwords immediately
- [ ] Delete `deployment_credentials.txt` after noting credentials
- [ ] Keep `docker.env` file secure and never commit to version control
- [ ] Set up firewall rules to restrict access
- [ ] Configure SSL/TLS certificates
- [ ] Set up regular database backups
- [ ] Monitor application logs
- [ ] Keep Docker images updated
- [ ] Use strong, unique passwords for all accounts

### Firewall Configuration (Ubuntu/Debian)

```bash
# Install UFW
sudo apt-get install ufw

# Allow SSH (adjust port as needed)
sudo ufw allow 22

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow OlgFeast ports (if not using reverse proxy)
sudo ufw allow 3000
sudo ufw allow 8000

# Enable firewall
sudo ufw enable
```

### SSL/TLS Setup with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Maintenance

### Health Monitoring

```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:3000/

# Monitor logs
docker-compose -f docker-compose.yml --env-file docker.env logs -f

# Check resource usage
docker stats
```

### Backup Strategy

```bash
#!/bin/bash
# backup.sh - Daily backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/olgfeast"
mkdir -p $BACKUP_DIR

# Database backup
docker-compose -f docker-compose.yml --env-file docker.env exec db pg_dump -U olgfeast olgfeast > $BACKUP_DIR/db_backup_$DATE.sql

# Environment backup
cp docker.env $BACKUP_DIR/env_backup_$DATE.env

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.env" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### Log Management

```bash
# View application logs
docker-compose -f docker-compose.yml --env-file docker.env logs backend
docker-compose -f docker-compose.yml --env-file docker.env logs frontend

# Rotate logs (configured in docker-compose.yml)
# Logs are automatically rotated with max 10MB per file and 3 files
```

## Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker status
docker info

# Check port conflicts
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Check logs
./first_time_setup.sh logs
```

#### Database Connection Issues
```bash
# Check database status
docker-compose -f docker-compose.yml --env-file docker.env exec db pg_isready -U olgfeast -d olgfeast

# Check database logs
docker-compose -f docker-compose.yml --env-file docker.env logs db
```

#### Frontend Not Loading
```bash
# Check frontend logs
docker-compose -f docker-compose.yml --env-file docker.env logs frontend

# Rebuild frontend
docker-compose -f docker-compose.yml --env-file docker.env build frontend
```

#### Memory Issues
```bash
# Check memory usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Or add swap space on Linux
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Performance Optimization

#### Production Optimizations

1. **Database Optimization**
   ```bash
   # Access database and run ANALYZE
   docker-compose -f docker-compose.yml --env-file docker.env exec db psql -U olgfeast -d olgfeast -c "ANALYZE;"
   ```

2. **Resource Limits**
   ```yaml
   # Add to docker-compose.yml services
   deploy:
     resources:
       limits:
         memory: 512M
         cpus: '0.5'
   ```

3. **Caching**
   - Redis is already configured for caching
   - Consider adding CDN for static assets

## Support

### Getting Help

1. **Check Logs**: Always check application logs first
2. **Review Documentation**: Check this guide and API documentation
3. **Community Support**: Check GitHub issues and discussions
4. **Professional Support**: Contact for enterprise support

### Useful Commands

```bash
# System information
docker system info
docker system df

# Clean up unused resources
docker system prune

# Update images
docker-compose -f docker-compose.yml --env-file docker.env pull
docker-compose -f docker-compose.yml --env-file docker.env up -d
```

## Conclusion

OlgFeast is now deployed and ready for production use! Remember to:

1. ✅ Change default passwords
2. ✅ Set up monitoring and backups
3. ✅ Configure SSL certificates
4. ✅ Review security settings
5. ✅ Test all functionality

For additional support or questions, refer to the documentation or contact the development team.

---

**Happy Cooking with OlgFeast! 🍽️**
