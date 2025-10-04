import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  User, 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest,
  FoodItem,
  FoodItemCreate,
  FoodItemGroup,
  CartItem,
  CartItemCreate,
  CartItemUpdate,
  CartSummary,
  Order,
  OrderCreate,
  OrderUpdate,
  OrderSummary,
  OrderAnalytics
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: 'http://localhost:8000/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor to handle token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await this.refreshToken(refreshToken);
              const { access_token } = response.data;
              
              localStorage.setItem('access_token', access_token);
              
              // Retry the original request
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<AxiosResponse<LoginResponse>> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    return this.api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  }

  async register(userData: RegisterRequest): Promise<AxiosResponse<User>> {
    return this.api.post('/auth/register', userData);
  }

  async refreshToken(refreshToken: string): Promise<AxiosResponse<LoginResponse>> {
    return this.api.post('/auth/refresh', { refresh_token: refreshToken });
  }

  async getCurrentUser(): Promise<AxiosResponse<User>> {
    return this.api.get('/auth/me');
  }

  // Menu endpoints
  async getFoodItems(skip = 0, limit = 100, foodGroup?: string): Promise<AxiosResponse<FoodItem[]>> {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (foodGroup) params.append('food_group', foodGroup);
    
    return this.api.get(`/menu/items?${params.toString()}`);
  }

  async getFoodGroups(): Promise<AxiosResponse<FoodItemGroup[]>> {
    return this.api.get('/menu/items/groups');
  }

  async getFoodItem(id: number): Promise<AxiosResponse<FoodItem>> {
    return this.api.get(`/menu/items/${id}`);
  }

  async createFoodItem(itemData: FoodItemCreate): Promise<AxiosResponse<FoodItem>> {
    return this.api.post('/menu/items', itemData);
  }

  async updateFoodItem(id: number, itemData: Partial<FoodItemCreate>): Promise<AxiosResponse<FoodItem>> {
    return this.api.put(`/menu/items/${id}`, itemData);
  }

  async deleteFoodItem(id: number): Promise<AxiosResponse<{ message: string }>> {
    return this.api.delete(`/menu/items/${id}`);
  }

  // Cart endpoints
  async getCartItems(): Promise<AxiosResponse<CartSummary>> {
    return this.api.get('/cart/items');
  }

  async addToCart(itemData: CartItemCreate): Promise<AxiosResponse<CartItem>> {
    return this.api.post('/cart/items', itemData);
  }

  async updateCartItem(id: number, itemData: CartItemUpdate): Promise<AxiosResponse<CartItem>> {
    return this.api.put(`/cart/items/${id}`, itemData);
  }

  async removeCartItem(id: number): Promise<AxiosResponse<{ message: string }>> {
    return this.api.delete(`/cart/items/${id}`);
  }

  async clearCart(): Promise<AxiosResponse<{ message: string }>> {
    return this.api.delete('/cart/clear');
  }

  async increaseItemQuantity(id: number): Promise<AxiosResponse<{ message: string; item: CartItem }>> {
    return this.api.post(`/cart/items/${id}/increase`);
  }

  async decreaseItemQuantity(id: number): Promise<AxiosResponse<{ message: string; item?: CartItem }>> {
    return this.api.post(`/cart/items/${id}/decrease`);
  }

  // Order endpoints
  async createOrder(orderData: OrderCreate): Promise<AxiosResponse<Order>> {
    return this.api.post('/orders/checkout', orderData);
  }

  async getMyOrders(skip = 0, limit = 50): Promise<AxiosResponse<OrderSummary[]>> {
    return this.api.get(`/orders/my-orders?skip=${skip}&limit=${limit}`);
  }

  async getMyOrder(id: number): Promise<AxiosResponse<Order>> {
    return this.api.get(`/orders/my-orders/${id}`);
  }

  async getAllOrders(skip = 0, limit = 50, status?: string): Promise<AxiosResponse<Order[]>> {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (status) params.append('status', status);
    
    return this.api.get(`/orders?${params.toString()}`);
  }

  async getOrder(id: number): Promise<AxiosResponse<Order>> {
    return this.api.get(`/orders/${id}`);
  }

  async updateOrderStatus(id: number, orderUpdate: OrderUpdate): Promise<AxiosResponse<Order>> {
    return this.api.put(`/orders/${id}/status`, orderUpdate);
  }

  async getOrderAnalytics(): Promise<AxiosResponse<OrderAnalytics>> {
    return this.api.get('/orders/analytics/dashboard');
  }

  // Operations endpoints
  async getPendingOrders(): Promise<AxiosResponse<Order[]>> {
    return this.api.get('/operations/orders/pending');
  }

  async getPreparingOrders(): Promise<AxiosResponse<Order[]>> {
    return this.api.get('/operations/orders/preparing');
  }

  async getReadyOrders(): Promise<AxiosResponse<Order[]>> {
    return this.api.get('/operations/orders/ready');
  }

  async getCompletedOrders(skip = 0, limit = 20): Promise<AxiosResponse<OrderSummary[]>> {
    return this.api.get(`/operations/orders/completed?skip=${skip}&limit=${limit}`);
  }

  async getOperationsAnalytics(): Promise<AxiosResponse<any>> {
    return this.api.get('/operations/dashboard/analytics');
  }
}

export const apiService = new ApiService();
export default apiService;
