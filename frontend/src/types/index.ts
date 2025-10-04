// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

// User Types
export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  created_at: string;
  updated_at?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  is_active?: boolean;
}

// Menu Types
export interface FoodItem {
  id: number;
  food_group: string;
  name: string;
  value: number;
  ticket: number;
  description?: string;
  is_available: boolean;
  created_at: string;
  updated_at?: string;
}

export interface FoodItemCreate {
  food_group: string;
  name: string;
  value: number;
  ticket: number;
  description?: string;
  is_available?: boolean;
}

export interface FoodItemGroup {
  group: string;
  items: FoodItem[];
}

// Cart Types
export interface CartItem {
  id: number;
  cart_id: number;
  food_item_id: number;
  quantity: number;
  created_at: string;
  updated_at?: string;
  food_item: FoodItem;
}

export interface CartItemCreate {
  food_item_id: number;
  quantity: number;
}

export interface CartItemUpdate {
  quantity: number;
}

export interface CartSummary {
  total_items: number;
  total_value: number;
  total_tickets: number;
  items: CartItem[];
}

// Order Types
export interface OrderItem {
  id: number;
  order_id: number;
  food_item_id: number;
  quantity: number;
  created_at: string;
  food_item: FoodItem;
}

export interface Order {
  id: number;
  ref_code: string;
  user_id: number;
  customer_name: string;
  status: OrderStatus;
  date_ordered: string;
  date_preparing?: string;
  date_ready?: string;
  date_complete?: string;
  last_status_change: string;
  order_items: OrderItem[];
}

export enum OrderStatus {
  PENDING = 'pending',
  PREPARING = 'preparing',
  READY = 'ready',
  COMPLETE = 'complete'
}

export interface OrderCreate {
  customer_name: string;
}

export interface OrderUpdate {
  status?: OrderStatus;
}

export interface OrderSummary {
  id: number;
  ref_code: string;
  customer_name: string;
  status: string;
  total_value: number;
  total_tickets: number;
  item_count: number;
  date_ordered: string;
}

export interface OrderAnalytics {
  total_orders: number;
  orders_today: number;
  orders_this_week: number;
  orders_this_month: number;
  status_counts: Record<string, number>;
  total_revenue: number;
  revenue_today: number;
  revenue_this_week: number;
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
  message?: string;
}

export interface OrderUpdateMessage {
  order_id: number;
  ref_code: string;
  customer_name: string;
  status: string;
  total_value: number;
  total_tickets: number;
  item_count: number;
  date_ordered: string;
  date_preparing?: string;
  date_ready?: string;
  date_complete?: string;
}

export interface KitchenUpdateMessage {
  pending_orders: any[];
  preparing_orders: any[];
  ready_orders: any[];
  timestamp: string;
}

export interface KitchenDisplayOrder {
  id: number;
  ref_code: string;
  customer_name: string;
  status: string;
  date_ordered: string;
  date_preparing?: string;
  date_ready?: string;
  items: Array<{
    name: string;
    quantity: number;
  }>;
  total_value: number;
  total_tickets: number;
}

export interface KitchenDisplayUpdate {
  pending_orders: KitchenDisplayOrder[];
  preparing_orders: KitchenDisplayOrder[];
  ready_orders: KitchenDisplayOrder[];
}

export interface AdminDashboardAnalytics {
  total_orders: number;
  orders_today: number;
  orders_this_week: number;
  orders_this_month: number;
  total_completed_orders: number;
  status_counts: Record<string, number>;
  total_revenue: number;
  timing_analytics: {
    avg_preparation_time: number;
    avg_total_time: number;
  };
}

export interface AdminDashboardOrder {
  id: number;
  ref_code: string;
  customer_name: string;
  status: string;
  date_ordered: string;
  date_preparing?: string;
  date_ready?: string;
  date_complete?: string;
  total_value: number;
  order_items: Array<{
    food_item_name: string;
    quantity: number;
  }>;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
