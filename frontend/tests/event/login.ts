import { expect, Page } from '@playwright/test';

// All browser projects share one client address. Respect the production login
// rate limit while still exercising the actual sign-in form and proxy.
export async function submitLogin(page: Page) {
  for (let attempt = 0; attempt < 5; attempt++) {
    const responsePromise = page.waitForResponse(response =>
      new URL(response.url()).pathname === '/api/v1/auth/login' &&
      response.request().method() === 'POST');
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    const response = await responsePromise;
    if (response.status() !== 429) {
      expect(response.ok(), `Sign-in returned ${response.status()}`).toBeTruthy();
      return;
    }
    await page.waitForTimeout(6100);
  }
  throw new Error('Sign-in remained rate limited after five attempts');
}
