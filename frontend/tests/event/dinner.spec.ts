import { test, expect } from '@playwright/test';
import { submitLogin } from './login';

test('volunteer tablet checkout, kitchen service, and depletion report', async ({ page, request }, info) => {
  const password = process.env.E2E_ADMIN_PASSWORD;
  if (!password) throw new Error('Set E2E_ADMIN_PASSWORD for an isolated test database');
  const api = process.env.E2E_API_URL || 'http://127.0.0.1:8002';
  const response = await request.post(`${api}/api/v1/auth/login`, { form: { username: 'admin', password } });
  expect(response.ok()).toBeTruthy();
  const headers = { Authorization: `Bearer ${(await response.json()).access_token}` };
  const suffix = `${Date.now()}-${info.project.name}`;
  async function create(path: string, data: unknown) {
    const result = await request.post(`${api}/api/v1${path}`, { headers, data });
    expect(result.ok(), await result.text()).toBeTruthy(); return result.json();
  }
  const event = await create('/events', { name: `Test dinner ${suffix}`, event_date: '2026-09-17', collect_tickets: true });
  const food = await create('/menu/items', { name: `Pasta ${Date.now()}`, food_group: `Dinner ${event.id}`, ticket: 3, value: 0, is_available: true });
  const ingredient = await create('/events/setup/consumables', { name: `Pasta ingredient ${suffix}`, unit: 'g' });
  const recipe = await request.put(`${api}/api/v1/events/setup/recipes/${food.id}`, { headers, data: [{ consumable_id: ingredient.id, quantity: 125 }] });
  expect(recipe.ok()).toBeTruthy();
  await create(`/events/${event.id}/stock`, { consumable_id: ingredient.id, quantity: 1000, reason: 'Starting stock' });
  const pageErrors: string[] = [];
  page.on('pageerror', e => pageErrors.push(e.message));
  await page.goto('/login');
  await page.getByLabel('Username', { exact: true }).fill('admin');
  await page.getByLabel('Password', { exact: true }).fill(password);
  await submitLogin(page);
  await expect(page).toHaveURL(/\/event$/);
  await page.getByLabel('Current event').selectOption(String(event.id));
  await page.getByLabel('Filter menu').selectOption(`Dinner ${event.id}`);
  const tile = page.getByRole('button', { name: `Add ${food.name}`, exact: true });
  await tile.click(); await tile.click();
  const target = await tile.boundingBox(); expect(target!.height).toBeGreaterThanOrEqual(48);
  await page.getByPlaceholder('Walk-up').fill('Table 8');
  await page.getByRole('button', { name: /Check order ·/ }).click();
  await expect(page.getByRole('button', { name: 'Send to kitchen', exact: true })).toBeDisabled();
  await page.getByLabel('I collected 6 tickets').check();
  await page.getByRole('button', { name: 'Send to kitchen', exact: true }).click();
  await expect(page.getByText('Sent to kitchen', { exact: true })).toBeVisible();
  await expect(page.getByText('Table 8 · 6 tickets collected')).toBeVisible();
  await page.getByRole('button', { name: 'Kitchen', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Table 8' })).toBeVisible();
  for (const name of ['Start preparing', 'Mark ready', 'Mark served']) {
    await page.getByRole('button', { name, exact: true }).click();
  }
  await page.getByRole('button', { name: 'Event report', exact: true }).click();
  const row = page.getByRole('row').filter({ hasText: ingredient.name });
  await expect(row).toContainText('250'); await expect(row).toContainText('750');
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download CSV' }).click();
  expect((await download).suggestedFilename()).toBe(`event-${event.id}-report.csv`);
  await page.getByRole('button', { name: 'Menu & setup', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Recipe per portion' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({path:`test-results/${info.project.name}.png`,fullPage:true});
  expect(pageErrors).toEqual([]);
});

test('guest tablet hands off physical tickets to a volunteer before preparation', async ({ page, request }, info) => {
  const password = process.env.E2E_ADMIN_PASSWORD!;
  const api = process.env.E2E_API_URL || 'http://127.0.0.1:8002';
  const login = await request.post(`${api}/api/v1/auth/login`, { form: { username: 'admin', password } });
  expect(login.ok()).toBeTruthy();
  const headers = { Authorization: `Bearer ${(await login.json()).access_token}` };
  const suffix = String(Date.now());
  async function post(path: string, data: unknown) {
    const result = await request.post(`${api}/api/v1${path}`, { headers, data });
    expect(result.ok(), await result.text()).toBeTruthy(); return result.json();
  }
  const event = await post('/events', { name: `Guest dinner ${suffix}`, event_date: '2026-09-17', collect_tickets: true });
  const food = await post('/menu/items', { name: `Guest pasta ${suffix}`, food_group: 'Dinner', ticket: 4, value: 0, is_available: true });
  const guest = `tablet-${suffix}`;
  await post('/auth/guest-stations', { username: guest, password: 'test-tablet-password' });
  async function signIn(username: string, pass: string) {
    await page.goto('/login');
    await page.getByLabel('Username', { exact: true }).fill(username);
    await page.getByLabel('Password', { exact: true }).fill(pass);
    await submitLogin(page);
    await expect(page).toHaveURL(/\/event$/);
    await page.getByLabel('Current event').selectOption(String(event.id));
  }
  await signIn(guest, 'test-tablet-password');
  await expect(page.getByRole('button', { name: 'Kitchen', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Menu & setup', exact: true })).toHaveCount(0);
  await page.getByLabel('Filter menu').selectOption('Dinner');
  const guestTile = page.getByRole('button', { name: `Add ${food.name}`, exact: true });
  while (!await guestTile.count()) await page.getByRole('button', {name:'Next',exact:true}).click();
  await guestTile.click();
  await expect(page.getByRole('checkbox')).toHaveCount(0);
  await page.getByRole('button', { name: /Check order ·/ }).click();
  await page.getByRole('button', { name: 'Send to ticket desk' }).click();
  await expect(page.getByText('Bring this number to the ticket desk')).toBeVisible();
  await page.reload();
  await expect(page.getByText('Bring this number to the ticket desk')).toBeVisible();
  const reportBefore = await request.get(`${api}/api/v1/events/${event.id}/report`, { headers });
  expect((await reportBefore.json()).order_count).toBe(0);
  await page.getByRole('button', { name: 'Sign out' }).click();
  await signIn('admin', password);
  await page.getByRole('button', { name: 'Kitchen', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Start preparing' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Collect tickets', exact: true }).click();
  const confirm = page.getByRole('button', { name: 'Confirm tickets and send to kitchen' });
  await expect(confirm).toBeDisabled();
  await page.getByRole('checkbox', { name: /I collected 4 tickets/ }).check();
  await confirm.click();
  await expect(page.getByText(/tickets confirmed and sent to the kitchen/)).toBeVisible();
  await page.getByRole('button', { name: 'Kitchen', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Start preparing' })).toBeVisible();
  const reportAfter = await request.get(`${api}/api/v1/events/${event.id}/report`, { headers });
  expect((await reportAfter.json()).tickets_collected).toBe(4);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({ path: `test-results/guest-${info.project.name}.png`, fullPage: true });
});
