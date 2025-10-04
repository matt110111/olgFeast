import { test, expect } from '@playwright/test';

test.describe('API Integration Tests', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    // Login and get auth token
    const response = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: {
        username: 'admin',
        password: 'admin123'
      },
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    const data = await response.json();
    authToken = data.access_token;
  });

  test('authentication endpoints work correctly', async ({ request }) => {
    // Test login
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: {
        username: 'customer',
        password: 'customer123'
      },
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    expect(loginResponse.status()).toBe(200);
    const loginData = await loginResponse.json();
    expect(loginData).toHaveProperty('access_token');
    expect(loginData).toHaveProperty('token_type', 'bearer');

    // Test protected endpoint
    const meResponse = await request.get('http://localhost:8000/api/v1/auth/me', {
      headers: {
        'Authorization': `Bearer ${loginData.access_token}`
      }
    });
    
    expect(meResponse.status()).toBe(200);
    const userData = await meResponse.json();
    expect(userData).toHaveProperty('username', 'customer');
  });

  test('menu endpoints return correct data', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/menu/items');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);
    
    // Verify menu item structure
    const item = data[0];
    expect(item).toHaveProperty('id');
    expect(item).toHaveProperty('name');
    expect(item).toHaveProperty('description');
    expect(item).toHaveProperty('price');
    expect(item).toHaveProperty('value');
    expect(item).toHaveProperty('ticket');
  });

  test('cart operations work correctly', async ({ request }) => {
    // Add item to cart
    const addResponse = await request.post('http://localhost:8000/api/v1/cart/items', {
      data: {
        food_item_id: 1,
        quantity: 2
      },
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    expect(addResponse.status()).toBe(200);
    
    // Get cart
    const cartResponse = await request.get('http://localhost:8000/api/v1/cart', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    expect(cartResponse.status()).toBe(200);
    const cartData = await cartResponse.json();
    expect(cartData).toHaveProperty('items');
    expect(cartData.items.length).toBeGreaterThan(0);
  });

  test('order creation and management', async ({ request }) => {
    // Create order
    const orderResponse = await request.post('http://localhost:8000/api/v1/orders/checkout', {
      data: {
        customer_name: 'API Test Customer'
      },
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    expect(orderResponse.status()).toBe(200);
    const orderData = await orderResponse.json();
    expect(orderData).toHaveProperty('id');
    expect(orderData).toHaveProperty('ref_code');
    expect(orderData).toHaveProperty('status', 'pending');

    // Update order status
    const updateResponse = await request.put(`http://localhost:8000/api/v1/orders/${orderData.id}/status`, {
      data: {
        status: 'preparing'
      },
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    expect(updateResponse.status()).toBe(200);
    const updatedOrder = await updateResponse.json();
    expect(updatedOrder).toHaveProperty('status', 'preparing');
  });

  test('operations dashboard endpoints', async ({ request }) => {
    // Test analytics endpoint
    const analyticsResponse = await request.get('http://localhost:8000/api/v1/operations/dashboard/analytics', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    expect(analyticsResponse.status()).toBe(200);
    const analyticsData = await analyticsResponse.json();
    expect(analyticsData).toHaveProperty('current_status_counts');
    expect(analyticsData).toHaveProperty('activity_stats');
    expect(analyticsData).toHaveProperty('timing_analytics');

    // Test orders endpoint
    const ordersResponse = await request.get('http://localhost:8000/api/v1/operations/orders?limit=10', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    expect(ordersResponse.status()).toBe(200);
    const ordersData = await ordersResponse.json();
    expect(Array.isArray(ordersData)).toBe(true);
  });

  test('error handling and validation', async ({ request }) => {
    // Test invalid token
    const invalidTokenResponse = await request.get('http://localhost:8000/api/v1/auth/me', {
      headers: {
        'Authorization': 'Bearer invalid_token'
      }
    });
    
    expect(invalidTokenResponse.status()).toBe(401);

    // Test missing required fields
    const invalidOrderResponse = await request.post('http://localhost:8000/api/v1/orders/checkout', {
      data: {},
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    expect(invalidOrderResponse.status()).toBe(422);

    // Test unauthorized access
    const unauthorizedResponse = await request.get('http://localhost:8000/api/v1/operations/dashboard/analytics');
    expect(unauthorizedResponse.status()).toBe(401);
  });

  test('websocket endpoints are accessible', async ({ request }) => {
    // Test websocket endpoint accessibility (should return 101 for upgrade)
    const wsResponse = await request.get('http://localhost:8000/ws/kitchen/display');
    // WebSocket endpoints return 101 for successful upgrade or 426 for missing upgrade header
    expect([101, 426]).toContain(wsResponse.status());
  });
});
