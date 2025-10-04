import { WebSocketMessage } from '../types';

export type WebSocketEventHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private connections: Map<string, WebSocket> = new Map();
  private eventHandlers: Map<string, Set<WebSocketEventHandler>> = new Map();
  private reconnectAttempts: Map<string, number> = new Map();
  private healthCheckInterval: Map<string, NodeJS.Timeout> = new Map();
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second

  connect(endpoint: string): WebSocket {
    // Clean up existing connection if in bad state
    const existing = this.connections.get(endpoint);
    if (existing && existing.readyState !== WebSocket.OPEN) {
      existing.close();
      this.connections.delete(endpoint);
      this.clearHealthCheck(endpoint);
    }

    // Don't create new connection if we already have a healthy one
    if (existing && existing.readyState === WebSocket.OPEN) {
      return existing;
    }

    const ws = new WebSocket(`ws://${window.location.hostname}:8000${endpoint}`);
    
    ws.onopen = () => {
      console.log(`✅ WebSocket connected to ${endpoint}`);
      this.connections.set(endpoint, ws);
      this.reconnectAttempts.delete(endpoint); // Reset reconnect counter
      this.startHealthCheck(endpoint);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(endpoint, message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = (event) => {
      console.log(`❌ WebSocket disconnected from ${endpoint}`, event.code, event.reason);
      this.connections.delete(endpoint);
      this.clearHealthCheck(endpoint);
      
      // Attempt reconnection if not a clean close
      if (event.code !== 1000) {
        this.attemptReconnect(endpoint);
      }
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error on ${endpoint}:`, error);
    };

    return ws;
  }

  disconnect(endpoint: string) {
    const ws = this.connections.get(endpoint);
    if (ws) {
      ws.close(1000, 'Client disconnecting'); // Clean close
      this.connections.delete(endpoint);
      this.clearHealthCheck(endpoint);
    }
  }

  disconnectAll() {
    this.connections.forEach((ws, endpoint) => {
      ws.close(1000, 'Client disconnecting');
    });
    this.connections.clear();
    this.clearAllHealthChecks();
  }

  private attemptReconnect(endpoint: string) {
    const attempts = this.reconnectAttempts.get(endpoint) || 0;
    if (attempts >= this.maxReconnectAttempts) {
      console.error(`Max reconnection attempts reached for ${endpoint}`);
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, attempts); // Exponential backoff
    this.reconnectAttempts.set(endpoint, attempts + 1);

    console.log(`Reconnecting to ${endpoint} in ${delay}ms (attempt ${attempts + 1})`);
    
    setTimeout(() => {
      this.connect(endpoint);
    }, delay);
  }

  private startHealthCheck(endpoint: string) {
    // Clear existing health check
    this.clearHealthCheck(endpoint);
    
    const interval = setInterval(() => {
      const ws = this.connections.get(endpoint);
      if (ws && ws.readyState === WebSocket.OPEN) {
        // Send ping
        this.send(endpoint, { type: 'ping' });
      } else {
        // Connection is dead, attempt reconnect
        console.log(`Health check failed for ${endpoint}, attempting reconnect`);
        this.attemptReconnect(endpoint);
      }
    }, 30000); // Check every 30 seconds

    this.healthCheckInterval.set(endpoint, interval);
  }

  private clearHealthCheck(endpoint: string) {
    const interval = this.healthCheckInterval.get(endpoint);
    if (interval) {
      clearInterval(interval);
      this.healthCheckInterval.delete(endpoint);
    }
  }

  private clearAllHealthChecks() {
    this.healthCheckInterval.forEach((interval) => {
      clearInterval(interval);
    });
    this.healthCheckInterval.clear();
  }

  send(endpoint: string, message: any) {
    const ws = this.connections.get(endpoint);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }

  getConnection(endpoint: string): WebSocket | undefined {
    return this.connections.get(endpoint);
  }

  isConnected(endpoint: string): boolean {
    const ws = this.connections.get(endpoint);
    return ws ? ws.readyState === WebSocket.OPEN : false;
  }

  subscribe(endpoint: string, eventType: string, handler: WebSocketEventHandler) {
    if (!this.eventHandlers.has(endpoint)) {
      this.eventHandlers.set(endpoint, new Set());
    }
    this.eventHandlers.get(endpoint)!.add(handler);

    // Connect if not already connected
    this.connect(endpoint);
  }

  unsubscribe(endpoint: string, eventType: string, handler: WebSocketEventHandler) {
    const handlers = this.eventHandlers.get(endpoint);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.disconnect(endpoint);
      }
    }
  }

  private handleMessage(endpoint: string, message: WebSocketMessage) {
    const handlers = this.eventHandlers.get(endpoint);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in WebSocket event handler:', error);
        }
      });
    }
  }

  // Convenience methods for specific endpoints
  connectKitchenDisplay() {
    return this.connect('/ws/kitchen/display');
  }

  connectOrderUpdates() {
    return this.connect('/ws/orders/updates');
  }

  connectAdminDashboard() {
    return this.connect('/ws/admin/dashboard');
  }

  // Convenience methods for sending common messages
  ping(endpoint: string) {
    this.send(endpoint, { type: 'ping' });
  }

  requestKitchenUpdate() {
    this.send('/ws/kitchen/display', { type: 'request_update' });
  }

  subscribeToOrders(userId: number) {
    this.send('/ws/orders/updates', { 
      type: 'subscribe_orders', 
      user_id: userId 
    });
  }

  requestAnalytics() {
    this.send('/ws/admin/dashboard', { type: 'request_analytics' });
  }

  requestOrders() {
    this.send('/ws/admin/dashboard', { type: 'request_orders' });
  }
}

export const websocketService = new WebSocketService();
export default websocketService;
