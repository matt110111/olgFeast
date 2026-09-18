import { WebSocketMessage } from '../types';
import { apiService } from './api';
export type WebSocketEventHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private connections = new Map<string, WebSocket>();
  private eventHandlers = new Map<string, Set<WebSocketEventHandler>>();
  private timers = new Map<string, ReturnType<typeof setTimeout>>();
  private pings = new Map<string, ReturnType<typeof setInterval>>();
  private wanted = new Set<string>();

  connect(endpoint: string): WebSocket {
    this.wanted.add(endpoint);
    const existing = this.connections.get(endpoint);
    if (existing && existing.readyState < WebSocket.CLOSING) return existing;
    const url = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
    const ws = new WebSocket(`${url}${endpoint}`);
    this.connections.set(endpoint, ws);
    ws.onopen = async () => {
      try {
        await apiService.ensureSession();
        if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'authenticate', token: localStorage.getItem('access_token') }));
      } catch { ws.close(1008, 'Sign in required'); }
    };
    ws.onmessage = event => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'authenticated') {
          this.pings.set(endpoint, setInterval(() => this.ping(endpoint), 25000));
          if (endpoint === '/ws/orders/updates') this.send(endpoint, {type:'subscribe_orders'});
        }
        this.eventHandlers.get(endpoint)?.forEach(handler => handler(message));
      } catch { /* Ignore malformed messages; retain the existing view. */ }
    };
    ws.onclose = event => {
      if (this.connections.get(endpoint) !== ws) return;
      this.connections.delete(endpoint);
      clearInterval(this.pings.get(endpoint)); this.pings.delete(endpoint);
      if (this.wanted.has(endpoint) && event.code !== 1008 && event.code !== 1000) {
        this.timers.set(endpoint, setTimeout(() => {
          if (this.wanted.has(endpoint)) this.connect(endpoint);
        }, 3000));
      }
    };
    return ws;
  }
  disconnect(endpoint: string) {
    this.wanted.delete(endpoint);
    clearTimeout(this.timers.get(endpoint)); this.timers.delete(endpoint);
    clearInterval(this.pings.get(endpoint)); this.pings.delete(endpoint);
    const ws = this.connections.get(endpoint); this.connections.delete(endpoint);
    ws?.close(1000, 'Disconnected');
  }
  disconnectAll() { Array.from(this.wanted).forEach(endpoint => this.disconnect(endpoint)); }
  send(endpoint: string, message: unknown) {
    const ws = this.connections.get(endpoint);
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify(message));
  }
  getConnection(endpoint: string) { return this.connections.get(endpoint); }
  isConnected(endpoint: string) { return this.connections.get(endpoint)?.readyState === WebSocket.OPEN; }
  subscribe(endpoint: string, eventType: string, handler: WebSocketEventHandler) {
    if (!this.eventHandlers.has(endpoint)) this.eventHandlers.set(endpoint, new Set());
    this.eventHandlers.get(endpoint)!.add(handler); this.connect(endpoint);
  }
  unsubscribe(endpoint: string, eventType: string, handler: WebSocketEventHandler) {
    this.eventHandlers.get(endpoint)?.delete(handler);
    if (!this.eventHandlers.get(endpoint)?.size) this.disconnect(endpoint);
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
