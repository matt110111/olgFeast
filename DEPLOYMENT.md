# OlgFeast Production Deployment Guide

This guide covers setting up automatic deployment using GitHub Actions and GitHub Container Registry (ghcr.io) for the OlgFeast application.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [GitHub Setup](#github-setup)
- [Production Server Setup](#production-server-setup)
- [Deployment Options](#deployment-options)
- [Environment Configuration](#environment-configuration)
- [Manual Deployment](#manual-deployment)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)
- [Security Considerations](#security-considerations)

## Overview

The deployment system uses:
- **GitHub Actions**: Automatically builds Docker images on git push
- **GitHub Container Registry (ghcr.io)**: Stores built images (FREE)
- **Multi-architecture support**: Images built for both x86 (amd64) and ARM (arm64) devices
- **Production Server**: Pulls and runs the latest images (works on Raspberry Pi, servers, etc.)
- **Zero-downtime deployments**: Rolling updates with health checks

## Prerequisites

### GitHub Repository
- Public repository (for free GitHub Actions minutes)
- Admin access to repository settings

### Production Server
- Ubuntu/Debian/CentOS server with Docker installed
- SSH access with sudo privileges
- Internet connectivity
- At least 2GB RAM, 10GB disk space

### Supported Architectures
The Docker images are built for multiple architectures:
- **linux/amd64**: x86_64 servers, most cloud providers
- **linux/arm64**: ARM-based servers, Raspberry Pi 4+, Apple Silicon Macs

Your deployment will automatically use the correct architecture for your server.

## GitHub Setup

### 1. Create GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name: "OlgFeast Deployment"
4. Select scopes:
   - ✅ `write:packages` (to push to GitHub Container Registry)
   - ✅ `read:packages` (to pull from GitHub Container Registry)
   - ✅ `repo` (if using private repository)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again)

### 2. Add Repository Secrets

1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `GITHUB_TOKEN` | Your PAT token | For pushing to ghcr.io |
| `GITHUB_OWNER` | Your GitHub username | Used in image names |
| `DEPLOY_HOST` | Your server IP/domain | (Optional) For SSH deployment |
| `DEPLOY_KEY` | SSH private key | (Optional) For SSH deployment |

### 3. Enable GitHub Container Registry

1. Go to your repository → Settings → Actions → General
2. Under "Workflow permissions", select "Read and write permissions"
3. Check "Allow GitHub Actions to create and approve pull requests"

## Production Server Setup

### 1. Install Docker and Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes to take effect
```

### 2. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/olgFeast.git
cd olgFeast
```

### 3. Create Production Environment File

```bash
# Copy the template
cp docker.env docker.prod.env

# Edit with production values
nano docker.prod.env
```

**Required Environment Variables:**

```bash
# Database
POSTGRES_PASSWORD=your_secure_database_password
POSTGRES_USER=olgfeast
POSTGRES_DB=olgfeast

# Redis
REDIS_PASSWORD=your_secure_redis_password

# Security
SECRET_KEY=your_very_secure_secret_key_at_least_32_characters

# Environment
DEBUG=false
ENVIRONMENT=production

# GitHub Container Registry
GITHUB_OWNER=your_github_username
```

### 4. Login to GitHub Container Registry

```bash
# Login to ghcr.io (you'll need your GitHub username and PAT)
echo "YOUR_GITHUB_PAT_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

## Deployment Options

### Option 1: Automatic Deployment with Watchtower (Recommended)

Watchtower automatically checks for new images and updates containers.

1. **Enable Watchtower** in `docker-compose.prod.yml`:

```yaml
# Uncomment the watchtower section
watchtower:
  image: containrrr/watchtower
  container_name: olgfeast_watchtower
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - /etc/localtime:/etc/localtime:ro
  environment:
    - WATCHTOWER_POLL_INTERVAL=300  # Check every 5 minutes
    - WATCHTOWER_CLEANUP=true       # Remove old images
    - WATCHTOWER_INCLUDE_RESTARTING=true
    - WATCHTOWER_REVIVE_STOPPED=false
    - WATCHTOWER_LABEL_ENABLE=true
  restart: unless-stopped
  networks:
    - olgfeast_network
```

2. **Start the application:**

```bash
./deploy.sh deploy
```

### Option 2: Manual Deployment Script

Use the provided `deploy.sh` script for manual deployments:

```bash
# Full deployment
./deploy.sh deploy

# Pull latest images only
./deploy.sh pull

# Check status
./deploy.sh status

# Run health checks
./deploy.sh health

# Clean up old images
./deploy.sh cleanup
```

### Option 3: Webhook Deployment (Advanced)

Set up a webhook endpoint that triggers deployment when GitHub Actions completes.

## Environment Configuration

### Production Environment File (`docker.prod.env`)

```bash
# Database Configuration
POSTGRES_PASSWORD=super_secure_database_password_here
POSTGRES_USER=olgfeast
POSTGRES_DB=olgfeast

# Redis Configuration
REDIS_PASSWORD=super_secure_redis_password_here

# Application Security
SECRET_KEY=your_very_secure_secret_key_at_least_32_characters_long
DEBUG=false
ENVIRONMENT=production

# GitHub Container Registry
GITHUB_OWNER=your_github_username

# Optional: Cleanup settings
CLEANUP_UNUSED_IMAGES=false
```

### Security Best Practices

1. **Use strong passwords** (minimum 32 characters)
2. **Generate secure SECRET_KEY**:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. **Restrict file permissions**:
   ```bash
   chmod 600 docker.prod.env
   ```
4. **Use HTTPS** in production (set up reverse proxy with SSL)

## Manual Deployment

### Initial Deployment

```bash
# 1. Ensure you're in the project directory
cd /path/to/olgFeast

# 2. Set environment variable
export GITHUB_OWNER=your_github_username

# 3. Run deployment
./deploy.sh deploy
```

### Subsequent Deployments

After pushing to main branch:

```bash
# Option 1: Automatic (if using Watchtower)
# Nothing needed - updates automatically

# Option 2: Manual
./deploy.sh deploy

# Option 3: Just pull images
./deploy.sh pull
```

## Troubleshooting

### Common Issues

#### 1. Authentication Failed
```
Error: unauthorized: authentication required
```

**Solution:**
```bash
# Re-login to GitHub Container Registry
echo "YOUR_GITHUB_PAT_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

#### 2. Image Not Found
```
Error: manifest for ghcr.io/username/olgfeast-backend:latest not found
```

**Solutions:**
- Check if GitHub Actions workflow completed successfully
- Verify `GITHUB_OWNER` environment variable is correct
- Check if images are public or you have access permissions

#### 3. Health Check Failed
```
[ERROR] Health checks failed after 30 attempts
```

**Solutions:**
```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
```

#### 4. Database Connection Issues
```
sqlalchemy.exc.OperationalError: connection to server failed
```

**Solutions:**
```bash
# Check database container
docker-compose -f docker-compose.prod.yml logs db

# Verify database is accessible
docker-compose -f docker-compose.prod.yml exec db pg_isready -U olgfeast -d olgfeast
```

### Debugging Commands

```bash
# View all container logs
docker-compose -f docker-compose.prod.yml logs

# View specific service logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs db

# Check container status
docker-compose -f docker-compose.prod.yml ps

# Execute commands in containers
docker-compose -f docker-compose.prod.yml exec backend bash
docker-compose -f docker-compose.prod.yml exec db psql -U olgfeast -d olgfeast

# Check resource usage
docker stats

# View image information
docker images | grep olgfeast
```

## Rollback Procedures

### Automatic Rollback

```bash
# Rollback to previous version
./deploy.sh rollback
```

### Manual Rollback

```bash
# 1. Stop current containers
docker-compose -f docker-compose.prod.yml down

# 2. Find previous image tag
docker images | grep olgfeast-backend

# 3. Update docker-compose.prod.yml to use specific tag
# Change: ghcr.io/username/olgfeast-backend:latest
# To: ghcr.io/username/olgfeast-backend:main-abc1234

# 4. Start with previous version
docker-compose -f docker-compose.prod.yml up -d
```

### Emergency Rollback

```bash
# Quick rollback using backup
cp backups/docker-compose.prod.yml.backup.YYYYMMDD_HHMMSS docker-compose.prod.yml
docker-compose -f docker-compose.prod.yml up -d
```

## Security Considerations

### 1. Environment Variables
- Never commit `docker.prod.env` to git
- Use strong, unique passwords
- Rotate secrets regularly

### 2. Network Security
- Use firewall to restrict access
- Consider using reverse proxy (nginx/traefik)
- Enable HTTPS with SSL certificates

### 3. Container Security
- Run containers as non-root user
- Regularly update base images
- Scan images for vulnerabilities

### 4. Access Control
- Limit SSH access to production server
- Use SSH keys instead of passwords
- Monitor access logs

### 5. Backup Strategy
- Regular database backups
- Store backups in secure location
- Test backup restoration procedures

## Monitoring and Maintenance

### Health Monitoring

```bash
# Check application health
curl http://localhost:8000/health
curl http://localhost:3000/

# Monitor logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Regular Maintenance

```bash
# Weekly cleanup
./deploy.sh cleanup

# Check for updates
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}" | grep olgfeast

# Update base images (when needed)
docker-compose -f docker-compose.prod.yml pull
```

### Log Management

```bash
# Configure log rotation in docker-compose.prod.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Support

For issues and questions:
1. Check this documentation
2. Review GitHub Actions logs
3. Check container logs
4. Open an issue in the repository

---

**Remember:** Always test deployments in a staging environment before production!