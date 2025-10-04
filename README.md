# OlgFeast - Restaurant Management System

A modern, full-stack restaurant management system built with FastAPI and React. Features include menu management, order processing, kitchen display, and real-time updates via WebSocket.

## 🚀 Features

- **Menu Management**: Dynamic menu with categories and items
- **Order Processing**: Complete order lifecycle from cart to kitchen
- **Real-time Updates**: WebSocket-powered live order updates
- **Kitchen Display**: Real-time kitchen dashboard for staff
- **Admin Dashboard**: Comprehensive management interface
- **User Authentication**: Role-based access control (Customer/Staff)
- **Dark/Light Theme**: Modern UI with theme switching
- **Responsive Design**: Works on desktop and mobile devices

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.13)
- **Frontend**: React 18 with TypeScript
- **Database**: PostgreSQL
- **Cache/WebSocket**: Redis
- **Containerization**: Docker & Docker Compose
- **Styling**: Tailwind CSS

## 📋 Prerequisites

- Docker & Docker Compose
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/olgfeast.git
cd olgfeast
```

### 2. First-Time Setup

Run the automated setup script:

```bash
chmod +x first_time_setup.sh
./first_time_setup.sh
```

This script will:
- Generate secure environment variables
- Set up the database
- Create initial admin and customer accounts
- Start all services

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Default Login Credentials

The setup script will generate credentials and save them to `deployment_credentials.txt`. 

**Important**: Change these passwords after first login!

## 🛠️ Development

### Start Development Environment

```bash
./docker-dev.sh
```

This starts the application with:
- Hot-reloading for both frontend and backend
- Development-optimized settings
- Frontend on port 3001 (to avoid conflicts)

### Stop the Application

```bash
./docker-stop.sh
```

## 📁 Project Structure

```
olgfeast/
├── fastapi_app/          # Backend (FastAPI)
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core configuration
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── websocket/   # WebSocket handlers
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   └── requirements.txt
├── frontend/             # Frontend (React)
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── contexts/    # React contexts
│   │   ├── services/    # API services
│   │   └── types/       # TypeScript types
│   └── package.json
├── docker-compose.yml    # Production Docker setup
├── docker-compose.override.yml  # Development overrides
└── first_time_setup.sh   # Automated setup script
```

## 🔧 Configuration

### Environment Variables

Copy the example files and update with your values:

```bash
cp docker.env.example docker.env
cp fastapi_app/env.example fastapi_app/.env
```

### Security

- Change default passwords after setup
- Use strong, unique passwords for production
- Consider using environment-specific configurations
- Enable HTTPS in production

## 🧪 Testing

### Backend Tests

```bash
cd fastapi_app
python -m pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 🚀 Deployment

### Production Deployment

1. Set up your production environment variables
2. Configure your domain and SSL certificates
3. Update CORS settings for your domain
4. Run the setup script on your production server

### Docker Production

```bash
# Build and start in production mode
./docker-start.sh

# Stop and clean up
./docker-stop.sh
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [React](https://reactjs.org/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Containerized with [Docker](https://www.docker.com/)

## 📞 Support

If you have any questions or need help, please open an issue on GitHub.

---

**Note**: This is a demo application. For production use, ensure proper security measures, database backups, and monitoring are in place.