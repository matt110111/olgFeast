import { test, expect } from '@playwright/test';

test.describe('Performance and Load Testing', () => {
  test('page load performance benchmarks', async ({ page }) => {
    // Test home page load time
    const startTime = Date.now();
    await page.goto('/');
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(3000); // Should load within 3 seconds
    
    // Test login page load time
    const loginStartTime = Date.now();
    await page.goto('/login');
    const loginLoadTime = Date.now() - loginStartTime;
    
    expect(loginLoadTime).toBeLessThan(2000); // Should load within 2 seconds
    
    // Test dashboard load time after login
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    const dashboardStartTime = Date.now();
    await page.goto('/admin');
    const dashboardLoadTime = Date.now() - dashboardStartTime;
    
    expect(dashboardLoadTime).toBeLessThan(4000); // Should load within 4 seconds
  });

  test('API response time benchmarks', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Test API response times
    const apiTests = [
      { url: '/api/v1/menu/items', maxTime: 1000 },
      { url: '/api/v1/operations/dashboard/analytics', maxTime: 1500 },
      { url: '/api/v1/operations/orders?limit=20', maxTime: 1000 },
      { url: '/api/v1/operations/orders/pending', maxTime: 800 },
      { url: '/api/v1/operations/orders/preparing', maxTime: 800 },
      { url: '/api/v1/operations/orders/ready', maxTime: 800 }
    ];
    
    for (const apiTest of apiTests) {
      const startTime = Date.now();
      const response = await page.request.get(`http://localhost:8000${apiTest.url}`, {
        headers: {
          'Authorization': `Bearer ${await page.evaluate(() => localStorage.getItem('access_token'))}`
        }
      });
      const responseTime = Date.now() - startTime;
      
      expect(response.status()).toBe(200);
      expect(responseTime).toBeLessThan(apiTest.maxTime);
    }
  });

  test('concurrent user simulation', async ({ browser }) => {
    const concurrentUsers = 5;
    const pages = [];
    
    // Create multiple browser contexts
    for (let i = 0; i < concurrentUsers; i++) {
      const context = await browser.newContext();
      const page = await context.newPage();
      pages.push({ page, context });
    }
    
    // Simulate concurrent logins
    const loginPromises = pages.map(async ({ page }, index) => {
      await page.goto('/login');
      await page.fill('input[name="username"]', 'customer');
      await page.fill('input[name="password"]', 'customer123');
      await page.click('button[type="submit"]');
      return index;
    });
    
    const results = await Promise.all(loginPromises);
    expect(results).toHaveLength(concurrentUsers);
    
    // Simulate concurrent menu browsing
    const browsePromises = pages.map(async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('h1')).toContainText('Menu');
      return true;
    });
    
    const browseResults = await Promise.all(browsePromises);
    expect(browseResults.every(result => result === true)).toBe(true);
    
    // Cleanup
    for (const { context } of pages) {
      await context.close();
    }
  });

  test('memory usage and resource optimization', async ({ page }) => {
    // Monitor memory usage during extended use
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Navigate through multiple pages
    const pages = ['/admin', '/kitchen', '/', '/admin', '/kitchen'];
    
    for (const pageUrl of pages) {
      await page.goto(pageUrl);
      await page.waitForLoadState('networkidle');
      
      // Check for memory leaks (basic check)
      const performanceMetrics = await page.evaluate(() => {
        return {
          memory: (performance as any).memory?.usedJSHeapSize || 0,
          timestamp: Date.now()
        };
      });
      
      // Memory usage should not exceed 100MB for basic operations
      expect(performanceMetrics.memory).toBeLessThan(100 * 1024 * 1024);
    }
  });

  test('websocket connection performance', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Test WebSocket connection time
    const wsStartTime = Date.now();
    await page.goto('/kitchen');
    await expect(page.locator('[data-testid="websocket-status"]')).toContainText('Connected');
    const wsConnectionTime = Date.now() - wsStartTime;
    
    expect(wsConnectionTime).toBeLessThan(2000); // WebSocket should connect within 2 seconds
    
    // Test message round-trip time
    const messageStartTime = Date.now();
    await page.evaluate(() => {
      if (window.testWebSocket) {
        window.testWebSocket.send(JSON.stringify({ type: 'ping' }));
      }
    });
    
    await page.waitForFunction(() => window.testWebSocketPong === true, { timeout: 5000 });
    const messageRoundTrip = Date.now() - messageStartTime;
    
    expect(messageRoundTrip).toBeLessThan(1000); // Message round-trip should be under 1 second
  });

  test('large dataset handling', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Test with large order limit
    const startTime = Date.now();
    const response = await page.request.get('http://localhost:8000/api/v1/operations/orders?limit=100', {
      headers: {
        'Authorization': `Bearer ${await page.evaluate(() => localStorage.getItem('access_token'))}`
      }
    });
    const responseTime = Date.now() - startTime;
    
    expect(response.status()).toBe(200);
    expect(responseTime).toBeLessThan(2000); // Large dataset should load within 2 seconds
    
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });

  test('error recovery and resilience', async ({ page }) => {
    // Test application resilience to network issues
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Simulate network interruption
    await page.context().setOffline(true);
    await page.goto('/admin');
    
    // Should show appropriate error state
    await expect(page.locator('text=Network Error')).toBeVisible();
    
    // Restore network and verify recovery
    await page.context().setOffline(false);
    await page.reload();
    
    // Should recover and load normally
    await expect(page.locator('h1')).toContainText('Admin Dashboard');
  });
});
