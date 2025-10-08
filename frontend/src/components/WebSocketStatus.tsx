import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff } from 'lucide-react';
import { websocketService } from '../services/websocket';

interface WebSocketStatusProps {
  endpoint: string;
  className?: string;
}

const WebSocketStatus: React.FC<WebSocketStatusProps> = ({ endpoint, className = '' }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');

  useEffect(() => {
    // Check initial connection status
    const ws = websocketService.getConnection?.(endpoint);
    if (ws && ws.readyState === WebSocket.OPEN) {
      setIsConnected(true);
      setConnectionStatus('connected');
    }

    // Subscribe to connection status updates
    const checkConnection = () => {
      const ws = websocketService.getConnection?.(endpoint);
      if (ws) {
        switch (ws.readyState) {
          case WebSocket.CONNECTING:
            setConnectionStatus('connecting');
            setIsConnected(false);
            break;
          case WebSocket.OPEN:
            setConnectionStatus('connected');
            setIsConnected(true);
            break;
          case WebSocket.CLOSING:
          case WebSocket.CLOSED:
            setConnectionStatus('disconnected');
            setIsConnected(false);
            break;
        }
      } else {
        setConnectionStatus('disconnected');
        setIsConnected(false);
      }
    };

    // Check connection status every 5 seconds
    const interval = setInterval(checkConnection, 5000);
    checkConnection(); // Initial check

    return () => clearInterval(interval);
  }, [endpoint]);

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connecting':
        return 'text-yellow-500';
      case 'connected':
        return 'text-green-500';
      case 'disconnected':
        return 'text-red-500';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connecting':
        return 'Connecting...';
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {isConnected ? (
        <Wifi className={`h-4 w-4 ${getStatusColor()}`} />
      ) : (
        <WifiOff className={`h-4 w-4 ${getStatusColor()}`} />
      )}
      <span className={`text-sm font-medium ${getStatusColor()}`}>
        {getStatusText()}
      </span>
    </div>
  );
};

export default WebSocketStatus;
