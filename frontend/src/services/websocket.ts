import { WebSocketMessage, OrderUpdateMessage, KitchenUpdateMessage } from '../types';

export type WebSocketEventHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private connections: Map<string, WebSocket> = new Map();
  private eventHandlers: Map<string, Set<WebSocketEventHandler>> = new Map();

  connect(endpoint: string): WebSocket {
    if (this.connections.has(endpoint)) {
      const existingConnection = this.connections.get(endpoint);
      if (existingConnection?.readyState === WebSocket.OPEN) {
        return existingConnection;
      }
    }

    const ws = new WebSocket(`ws://localhost:8000${endpoint}`);
    
    ws.onopen = () => {
      console.log(`✅ WebSocket connected to ${endpoint}`);
      this.connections.set(endpoint, ws);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(endpoint, message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log(`❌ WebSocket disconnected from ${endpoint}`);
      this.connections.delete(endpoint);
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error on ${endpoint}:`, error);
    };

    return ws;
  }

  disconnect(endpoint: string) {
    const ws = this.connections.get(endpoint);
    if (ws) {
      ws.close();
      this.connections.delete(endpoint);
    }
  }

  disconnectAll() {
    this.connections.forEach((ws, endpoint) => {
      ws.close();
    });
    this.connections.clear();
  }

  send(endpoint: string, message: any) {
    const ws = this.connections.get(endpoint);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }

  subscribe(endpoint: string, eventType: string, handler: WebSocketEventHandler) {
    const key = `${endpoint}:${eventType}`;
    if (!this.eventHandlers.has(key)) {
      this.eventHandlers.set(key, new Set());
    }
    this.eventHandlers.get(key)!.add(handler);

    // Connect if not already connected
    this.connect(endpoint);
  }

  unsubscribe(endpoint: string, eventType: string, handler: WebSocketEventHandler) {
    const key = `${endpoint}:${eventType}`;
    const handlers = this.eventHandlers.get(key);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.eventHandlers.delete(key);
        // Check if there are any other handlers for this endpoint
        const hasOtherHandlers = Array.from(this.eventHandlers.keys()).some(k => k.startsWith(`${endpoint}:`));
        if (!hasOtherHandlers) {
          this.disconnect(endpoint);
        }
      }
    }
  }

  private handleMessage(endpoint: string, message: WebSocketMessage) {
    // Call handlers for all event types for this endpoint
    const keysToCheck = [`${endpoint}:${message.type}`, `${endpoint}:*`];
    keysToCheck.forEach(key => {
      const handlers = this.eventHandlers.get(key);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error('Error in WebSocket event handler:', error);
          }
        });
      }
    });
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
