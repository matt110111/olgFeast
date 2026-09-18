import { test, expect } from '@playwright/test';

test.describe('Kitchen Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Check if already logged in, if not, log in as admin
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      // Fill login form
      await page.fill('input[name="username"]', 'admin');
      await page.fill('input[name="password"]', 'admin123');
      await page.click('button[type="submit"]');

      // Wait for navigation to home page
      await page.waitForURL('/');
    }
  });

  test('should display kitchen dashboard', async ({ page }) => {
    // Navigate to kitchen dashboard
    await page.goto('/kitchen');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Check if the kitchen dashboard is displayed
    await expect(page.locator('h1')).toContainText('Kitchen Display');

    // Check if order sections are present
    await expect(page.locator('text=Pending Orders')).toBeVisible();
    await expect(page.locator('text=Preparing')).toBeVisible();
    await expect(page.locator('text=Ready for Pickup')).toBeVisible();
  });

  test('should display orders in real-time', async ({ page }) => {
    // Navigate to kitchen dashboard
    await page.goto('/kitchen');

    // Wait for initial load
    await page.waitForLoadState('networkidle');

    // Check initial state (should show "No orders" or actual orders)
    const pendingSection = page.locator('.bg-yellow-500').locator('..');
    const preparingSection = page.locator('.bg-blue-500').locator('..');
    const readySection = page.locator('.bg-green-500').locator('..');

    // At least one section should be visible
    await expect(pendingSection.or(preparingSection).or(readySection)).toBeVisible();
  });

  test('should handle WebSocket connections', async ({ page }) => {
    // Navigate to kitchen dashboard
    await page.goto('/kitchen');

    // Wait for WebSocket connection
    await page.waitForLoadState('networkidle');

    // Check for live data indicator
    await expect(page.locator('text=Live Data')).toBeVisible();

    // Check for connected status indicator (green dot)
    const liveIndicator = page.locator('.bg-green-500');
    await expect(liveIndicator).toBeVisible();
  });
});

test.describe('Authentication Flow', () => {
  test('should login and access protected routes', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Fill and submit login form
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // Should redirect to home page
    await page.waitForURL('/');

    // Should be able to access kitchen dashboard
    await page.goto('/kitchen');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1')).toContainText('Kitchen Display');
  });
});

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('should display admin dashboard with analytics', async ({ page }) => {
    // Navigate to admin dashboard
    await page.goto('/admin');

    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Check for analytics cards
    await expect(page.locator('text=Total Orders')).toBeVisible();
    await expect(page.locator('text=Today\'s Orders')).toBeVisible();
    await expect(page.locator('text=Completed Orders')).toBeVisible();

    // Check for orders table
    await expect(page.locator('text=Recent Orders')).toBeVisible();
  });

  test('should handle order status updates', async ({ page }) => {
    // Navigate to admin dashboard
    await page.goto('/admin');

    // Wait for orders to load
    await page.waitForLoadState('networkidle');

    // Look for any order status buttons
    const statusButtons = page.locator('button:has-text("Mark")');
    const buttonCount = await statusButtons.count();

    if (buttonCount > 0) {
      // Click the first status update button
      await statusButtons.first().click();

      // Wait for the update to process
      await page.waitForTimeout(1000);

      // The page should still be functional (no errors)
      await expect(page.locator('h1')).toContainText('Admin Dashboard');
    }
  });
});
