# WebSocket Implementation for Kitchen Display

This document describes the real-time WebSocket implementation for the olgFeast kitchen display system, which eliminates the need for page refreshes and provides instant updates when orders are created or status changes occur.

## 🚀 Features

- **Real-time order updates**: New orders appear instantly on kitchen displays
- **Status change notifications**: Order status changes are broadcast to relevant stations
- **Automatic reconnection**: WebSocket connections automatically reconnect if dropped
- **Fallback polling**: Falls back to 10-second polling if WebSocket fails
- **Connection status indicator**: Visual indicator shows connection status
- **Smooth animations**: Orders slide in/out with smooth transitions

## 🏗️ Architecture

### Components

1. **Django Channels**: WebSocket framework for Django
2. **Redis**: Message broker for WebSocket communication
3. **WebSocket Consumer**: Handles real-time communication
4. **API Endpoints**: RESTful endpoints for order status updates
5. **Frontend JavaScript**: WebSocket client with fallback mechanisms

### Data Flow

```
Order Created → WebSocket Notification → Kitchen Display Update
     ↓
Status Changed → WebSocket Notification → Station Updates
     ↓
Connection Lost → Auto Reconnect → Fallback to Polling
```

## 📁 Files Added/Modified

### New Files
- `olgFeast/asgi.py` - ASGI configuration for WebSocket support
- `operations/routing.py` - WebSocket URL routing
- `operations/consumers.py` - WebSocket consumer for kitchen displays
- `setup_websockets.sh` - Installation script for Redis and dependencies

### Modified Files
- `requirements.txt` - Added channels and channels-redis
- `olgFeast/settings.py` - Added Channels configuration
- `operations/views.py` - Added WebSocket notifications and API endpoints
- `operations/urls.py` - Added API endpoint routes
- `shopping_cart/views.py` - Added new order notifications
- `operations/templates/operations/station_display.html` - Replaced auto-refresh with WebSocket client

## 🔧 Installation

### 1. Run the Setup Script
```bash
./setup_websockets.sh
```

### 2. Manual Installation (Alternative)

#### Install Redis
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis
```

#### Install Python Dependencies
```bash
pip install channels==4.0.0 channels-redis==4.2.0
```

### 3. Run Migrations
```bash
python manage.py migrate
```

## 🚀 Running the Application

### Development
```bash
python manage.py runserver
```

### Production (with WebSocket support)
```bash
daphne -b 0.0.0.0 -p 8000 olgFeast.asgi:application
```

## 🌐 WebSocket Endpoints

### Kitchen Display WebSockets
- **Pending Orders**: `ws://localhost:8000/ws/kitchen/pending/`
- **Preparing Orders**: `ws://localhost:8000/ws/kitchen/preparing/`
- **Ready Orders**: `ws://localhost:8000/ws/kitchen/ready/`

### API Endpoints
- **Update Order Status**: `POST /operations/api/orders/{order_id}/status/`

## 📱 Usage

### Kitchen Display
1. Navigate to `http://localhost:8000/operations/stations/`
2. Click "Open Display" for any station
3. The display will connect via WebSocket and show real-time updates
4. Connection status is shown in the bottom-right corner

### Order Management
1. Staff can update order status through the admin interface
2. Status changes are automatically broadcast to relevant kitchen displays
3. New orders appear instantly on the pending station display

## 🔄 Message Types

### WebSocket Messages

#### `orders_update`
Sent when initial connection is established or full refresh is requested.
```json
{
  "type": "orders_update",
  "orders": [...],
  "station": "pending"
}
```

#### `order_update`
Sent when a new order is created or an existing order is modified.
```json
{
  "type": "order_update",
  "order": {...},
  "action": "new_order" | "status_changed"
}
```

#### `status_change`
Sent when an order's status changes.
```json
{
  "type": "status_change",
  "order_id": 123,
  "old_status": "pending",
  "new_status": "preparing"
}
```

## 🛡️ Error Handling

### Connection Management
- **Automatic Reconnection**: Up to 5 attempts with exponential backoff
- **Fallback Polling**: 10-second page refresh if WebSocket fails completely
- **Connection Status**: Visual indicator shows current connection state

### Error States
- **Connected**: Green WiFi icon
- **Disconnected**: Red WiFi-slash icon
- **Reconnecting**: Spinning sync icon
- **Error**: Warning triangle icon
- **Failed**: Red X icon (fallback to polling)

## 🔧 Configuration

### Redis Configuration
Default Redis connection settings in `settings.py`:
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### WebSocket Settings
- **Reconnection attempts**: 5 maximum
- **Reconnection delay**: Exponential backoff (1s, 2s, 4s, 8s, 16s, 30s max)
- **Fallback polling**: 10 seconds

## 🧪 Testing

### Manual Testing
1. Open multiple kitchen display tabs
2. Create a new order from the customer interface
3. Verify the order appears instantly on the pending display
4. Update the order status through admin interface
5. Verify the order moves between displays in real-time

### Connection Testing
1. Disconnect network temporarily
2. Verify reconnection attempts are shown
3. Reconnect network
4. Verify connection is restored

## 🚀 Performance Considerations

### Scalability
- **Redis**: Can handle thousands of concurrent connections
- **Django Channels**: Efficient async WebSocket handling
- **Message Broadcasting**: Only sends updates to relevant stations

### Optimization
- **Order Limit**: Displays show maximum 20 recent orders
- **Efficient Queries**: Database queries are optimized for real-time updates
- **Minimal Data Transfer**: Only necessary order data is transmitted

## 🔒 Security

### Authentication
- WebSocket connections inherit Django session authentication
- API endpoints require proper permissions
- CSRF protection on form submissions

### Data Validation
- All incoming WebSocket messages are validated
- Order status changes are restricted to valid transitions
- Input sanitization prevents XSS attacks

## 🐛 Troubleshooting

### Common Issues

#### Redis Connection Failed
```bash
# Check if Redis is running
redis-cli ping

# Start Redis service
brew services start redis  # macOS
sudo systemctl start redis  # Linux
```

#### WebSocket Connection Failed
1. Check browser console for errors
2. Verify Redis is running
3. Check Django server logs
4. Ensure ASGI application is configured correctly

#### Orders Not Updating
1. Check WebSocket connection status
2. Verify order status updates are being saved
3. Check Django server logs for WebSocket errors
4. Test with browser developer tools

### Debug Mode
Enable debug logging in `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'channels': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📈 Future Enhancements

### Potential Improvements
1. **Order Priority**: Visual indicators for high-priority orders
2. **Sound Notifications**: Audio alerts for new orders
3. **Mobile App**: Native mobile app for kitchen staff
4. **Analytics**: Real-time order analytics and metrics
5. **Multi-location**: Support for multiple restaurant locations
6. **Order Timing**: Automatic timing calculations and alerts

### Technical Improvements
1. **Message Queuing**: Use Celery for background tasks
2. **Caching**: Redis caching for improved performance
3. **Load Balancing**: Multiple Redis instances for high availability
4. **Monitoring**: WebSocket connection monitoring and alerting

## 📞 Support

For issues or questions regarding the WebSocket implementation:
1. Check the troubleshooting section above
2. Review Django Channels documentation
3. Check Redis server status and logs
4. Verify all dependencies are correctly installed

---

**Note**: This implementation provides a robust, real-time communication system for the kitchen display. The fallback mechanisms ensure the system remains functional even if WebSocket connections fail, maintaining the reliability required for a restaurant environment.
