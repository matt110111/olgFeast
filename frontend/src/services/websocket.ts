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
