import { test, expect } from '@playwright/test';

test.describe('Comprehensive E2E Restaurant Management System', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('complete restaurant workflow - customer to kitchen to admin', async ({ page }) => {
    // 1. Customer Login
    await page.click('text=Login');
    await page.fill('input[name="username"]', 'customer');
    await page.fill('input[name="password"]', 'customer123');
    await page.click('button[type="submit"]');
    
    // Wait for redirect to home
    await expect(page).toHaveURL('/');
    
    // 2. Browse Menu and Add Items to Cart
    await expect(page.locator('h1')).toContainText('Menu');
    
    // Add first item to cart
    const firstItem = page.locator('[data-testid="menu-item"]').first();
    await firstItem.locator('button').click();
    
    // Verify cart has items
    await page.click('text=Cart');
    await expect(page.locator('[data-testid="cart-item"]')).toHaveCount.atLeast(1);
    
    // 3. Create Order
    await page.click('text=Checkout');
    await page.fill('input[name="customer_name"]', 'Test Customer');
    await page.click('button[type="submit"]');
    
    // Wait for order confirmation
    await expect(page.locator('text=Order created successfully')).toBeVisible();
    
    // 4. Admin Login for Kitchen Management
    await page.click('text=Logout');
    await page.click('text=Login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // 5. Check Kitchen Dashboard
    await page.click('text=Kitchen');
    await expect(page).toHaveURL('/kitchen');
    
    // Verify kitchen displays orders
    await expect(page.locator('h1')).toContainText('Kitchen Display');
    await expect(page.locator('[data-testid="order-card"]')).toHaveCount.atLeast(1);
    
    // 6. Update Order Status
    const orderCard = page.locator('[data-testid="order-card"]').first();
    await orderCard.locator('button').click(); // Mark as preparing
    
    // Verify status update
    await expect(orderCard.locator('[data-testid="status-badge"]')).toContainText('Preparing');
    
    // 7. Check Admin Dashboard
    await page.click('text=Admin');
    await expect(page).toHaveURL('/admin');
    
    // Verify analytics are displayed
    await expect(page.locator('h1')).toContainText('Admin Dashboard');
    await expect(page.locator('[data-testid="analytics-card"]')).toHaveCount.atLeast(3);
    
    // Verify order management
    await expect(page.locator('[data-testid="order-row"]')).toHaveCount.atLeast(1);
  });

  test('websocket real-time updates work correctly', async ({ page, context }) => {
    // Login as admin
    await page.click('text=Login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Open kitchen dashboard
    await page.click('text=Kitchen');
    await expect(page).toHaveURL('/kitchen');
    
    // Get initial order count
    const initialOrderCount = await page.locator('[data-testid="order-card"]').count();
    
    // Open second tab as customer
    const customerPage = await context.newPage();
    await customerPage.goto('/');
    
    // Login as customer
    await customerPage.click('text=Login');
    await customerPage.fill('input[name="username"]', 'customer');
    await customerPage.fill('input[name="password"]', 'customer123');
    await customerPage.click('button[type="submit"]');
    
    // Add item to cart and create order
    await customerPage.locator('[data-testid="menu-item"]').first().locator('button').click();
    await customerPage.click('text=Checkout');
    await customerPage.fill('input[name="customer_name"]', 'WebSocket Test Customer');
    await customerPage.click('button[type="submit"]');
    
    // Wait for order to appear in kitchen dashboard (real-time update)
    await expect(page.locator('[data-testid="order-card"]')).toHaveCount(initialOrderCount + 1);
    
    // Verify the new order appears
    await expect(page.locator('text=WebSocket Test Customer')).toBeVisible();
    
    await customerPage.close();
  });

  test('error handling and edge cases', async ({ page }) => {
    // Test invalid login
    await page.click('text=Login');
    await page.fill('input[name="username"]', 'invalid');
    await page.fill('input[name="password"]', 'invalid');
    await page.click('button[type="submit"]');
    
    // Should show error message
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
    
    // Test empty cart checkout
    await page.goto('/');
    await page.click('text=Login');
    await page.fill('input[name="username"]', 'customer');
    await page.fill('input[name="password"]', 'customer123');
    await page.click('button[type="submit"]');
    
    await page.click('text=Checkout');
    await page.fill('input[name="customer_name"]', 'Test');
    await page.click('button[type="submit"]');
    
    // Should show empty cart error
    await expect(page.locator('text=Cart is empty')).toBeVisible();
  });

  test('responsive design works on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/');
    
    // Verify mobile navigation works
    await expect(page.locator('text=Menu')).toBeVisible();
    
    // Test mobile menu interaction
    await page.locator('[data-testid="mobile-menu-button"]').click();
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
    
    // Login on mobile
    await page.click('text=Login');
    await page.fill('input[name="username"]', 'customer');
    await page.fill('input[name="password"]', 'customer123');
    await page.click('button[type="submit"]');
    
    // Verify mobile layout
    await expect(page.locator('text=Menu')).toBeVisible();
  });

  test('performance and loading states', async ({ page }) => {
    // Test page load performance
    const startTime = Date.now();
    await page.goto('/');
    const loadTime = Date.now() - startTime;
    
    // Should load within reasonable time (5 seconds)
    expect(loadTime).toBeLessThan(5000);
    
    // Test loading states
    await page.click('text=Login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Check for loading spinner during navigation
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
    
    // Wait for page to load
    await expect(page).toHaveURL('/');
    await expect(page.locator('[data-testid="loading-spinner"]')).not.toBeVisible();
  });
});
