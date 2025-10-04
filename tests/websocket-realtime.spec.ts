import { test, expect } from '@playwright/test';

test.describe('WebSocket Real-Time Communication Tests', () => {
  test('kitchen display websocket connection and updates', async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Navigate to kitchen dashboard
    await page.goto('/kitchen');
    
    // Wait for WebSocket connection
    await page.waitForSelector('[data-testid="websocket-status"]');
    await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Connected');
    
    // Verify initial orders are loaded
    await expect(page.locator('[data-testid="order-card"]')).toHaveCount.atLeast(0);
    
    // Test WebSocket ping/pong
    await page.evaluate(() => {
      // Simulate WebSocket ping
      window.testWebSocketPing = true;
    });
    
    // Wait for pong response
    await page.waitForFunction(() => window.testWebSocketPong === true, { timeout: 5000 });
  });

  test('admin dashboard websocket connection and analytics updates', async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Navigate to admin dashboard
    await page.goto('/admin');
    
    // Wait for WebSocket connection
    await page.waitForSelector('[data-testid="websocket-status"]');
    await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Connected');
    
    // Verify analytics are loaded
    await expect(page.locator('[data-testid="analytics-card"]')).toHaveCount.atLeast(3);
    
    // Verify orders table is loaded
    await expect(page.locator('[data-testid="orders-table"]')).toBeVisible();
  });

  test('real-time order status updates broadcast correctly', async ({ page, context }) => {
    // Open admin dashboard
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.goto('/admin');
    
    // Open kitchen dashboard in second tab
    const kitchenPage = await context.newPage();
    await kitchenPage.goto('/login');
    await kitchenPage.fill('input[name="username"]', 'admin');
    await kitchenPage.fill('input[name="password"]', 'admin123');
    await kitchenPage.click('button[type="submit"]');
    await kitchenPage.goto('/kitchen');
    
    // Wait for both pages to load
    await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Connected');
    await expect(kitchenPage.locator('[data-testid="websocket-status"]')).toContainText('Connected');
    
    // Get initial order count
    const initialAdminOrders = await page.locator('[data-testid="order-row"]').count();
    const initialKitchenOrders = await kitchenPage.locator('[data-testid="order-card"]').count();
    
    // Update order status in admin dashboard
    if (initialAdminOrders > 0) {
      await page.locator('[data-testid="order-row"]').first().locator('button').click();
      
      // Wait for status update to propagate to kitchen
      await expect(kitchenPage.locator('[data-testid="order-card"]').first())
        .toContainText('Preparing', { timeout: 10000 });
    }
    
    await kitchenPage.close();
  });

  test('new order creation broadcasts to all connected clients', async ({ page, context }) => {
    // Open kitchen dashboard
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.goto('/kitchen');
    
    // Open admin dashboard in second tab
    const adminPage = await context.newPage();
    await adminPage.goto('/login');
    await adminPage.fill('input[name="username"]', 'admin');
    await adminPage.fill('input[name="password"]', 'admin123');
    await adminPage.click('button[type="submit"]');
    await adminPage.goto('/admin');
    
    // Wait for WebSocket connections
    await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Connected');
    await expect(adminPage.locator('[data-testid="websocket-status"]')).toContainText('Connected');
    
    // Get initial counts
    const initialKitchenOrders = await page.locator('[data-testid="order-card"]').count();
    const initialAdminOrders = await adminPage.locator('[data-testid="order-row"]').count();
    
    // Create new order in third tab
    const customerPage = await context.newPage();
    await customerPage.goto('/login');
    await customerPage.fill('input[name="username"]', 'customer');
    await customerPage.fill('input[name="password"]', 'customer123');
    await customerPage.click('button[type="submit"]');
    
    // Add item to cart and create order
    await customerPage.locator('[data-testid="menu-item"]').first().locator('button').click();
    await customerPage.click('text=Checkout');
    await customerPage.fill('input[name="customer_name"]', 'WebSocket Test Order');
    await customerPage.click('button[type="submit"]');
    
    // Wait for order to appear in both dashboards
    await expect(page.locator('[data-testid="order-card"]'))
      .toHaveCount(initialKitchenOrders + 1, { timeout: 10000 });
    await expect(adminPage.locator('[data-testid="order-row"]'))
      .toHaveCount(initialAdminOrders + 1, { timeout: 10000 });
    
    // Verify order details
    await expect(page.locator('text=WebSocket Test Order')).toBeVisible();
    await expect(adminPage.locator('text=WebSocket Test Order')).toBeVisible();
    
    await customerPage.close();
    await adminPage.close();
  });

  test('websocket reconnection handling', async ({ page }) => {
    // Login and connect to kitchen dashboard
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.goto('/kitchen');
    
    // Wait for initial connection
    await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Connected');
    
    // Simulate network interruption
    await page.context().setOffline(true);
    
    // Wait for disconnection status
    await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Disconnected');
    
    // Restore network
    await page.context().setOffline(false);
    
    // Wait for reconnection
    await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Connected', { timeout: 10000 });
  });

  test('websocket message validation and error handling', async ({ page }) => {
    // Login and connect
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.goto('/kitchen');
    
    // Wait for connection
    await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Connected');
    
    // Test invalid message handling
    await page.evaluate(() => {
      // Simulate sending invalid message
      if (window.testWebSocket) {
        window.testWebSocket.send('invalid json message');
      }
    });
    
    // Verify connection is still stable
    await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Connected');
    
    // Test ping/pong mechanism
    await page.evaluate(() => {
      if (window.testWebSocket) {
        window.testWebSocket.send(JSON.stringify({ type: 'ping' }));
      }
    });
    
    // Wait for pong response
    await page.waitForFunction(() => window.testWebSocketPong === true, { timeout: 5000 });
  });
});
