import { test, expect } from '@playwright/test';
import { submitLogin } from './login';

test('one check collects tickets and routes a full menu to four kitchens', async ({ page, request }, info) => {
  const api = process.env.E2E_API_URL || 'http://127.0.0.1:8002';
  const password = process.env.E2E_ADMIN_PASSWORD!;
  const login = await request.post(`${api}/api/v1/auth/login`, { form: { username: 'admin', password } });
  expect(login.ok()).toBeTruthy();
  const headers = { Authorization: `Bearer ${(await login.json()).access_token}` };
  async function write(method: 'post' | 'put', path: string, data: unknown) {
    const r = await request[method](`${api}/api/v1${path}`, { headers, data });
    expect(r.ok(), await r.text()).toBeTruthy(); return r.json();
  }
  const suffix = Date.now();
  const event = await write('post', '/events', { name: `Four kitchens ${suffix}`, event_date: '2026-09-26' });
  const rooms = [];
  const foods = [];
  for (const [index, name] of ['Fried', 'Grilled', 'Cooked 1', 'Cooked 2'].entries()) {
    const room = await write('post', `/events/${event.id}/rooms`, { name });
    const food = await write('post', '/menu/items', { name: `${name} meal ${suffix}`, food_group: 'Dinner', ticket: index + 1, value: 0, is_available: true });
    await write('put', `/events/${event.id}/rooms/${room.id}/menu`, { food_item_ids: [food.id] });
    rooms.push(room); foods.push(food);
  }
  await page.goto('/login');
  await page.getByLabel('Username', { exact: true }).fill('admin');
  await page.getByLabel('Password', { exact: true }).fill(password);
  await submitLogin(page);
  await expect(page).toHaveURL(/\/event$/);
  await page.getByLabel('Current event').selectOption(String(event.id));
  await page.getByLabel('Input station').selectOption('6');
  for (const [index, food] of foods.entries()) {
    await page.getByLabel('Filter menu').selectOption(rooms[index].name);
    await page.getByRole('button', { name: `Add ${food.name}`, exact: true }).click();
  }
  await page.getByPlaceholder('Walk-up').fill('Four kitchen table');
  // A second input has an independent draft, even on the same browser.
  await page.getByLabel('Input station').selectOption('1');
  await expect(page.getByText('Tap a menu item to begin.')).toBeVisible();
  await page.getByLabel('Input station').selectOption('6');
  const check = page.getByRole('button', { name: 'Check order · 10 tickets' });
  await expect(check).toBeInViewport({ratio:1});
  await check.click();
  const send = page.getByRole('button', { name: 'Send to kitchen', exact: true });
  await expect(send).toBeDisabled();
  await expect(send).toBeInViewport({ratio:1});
  await page.getByLabel('I collected 10 tickets').check();
  await send.click();
  await expect(page.getByText('Sent to kitchen', { exact: true })).toBeVisible();
  await expect(page.getByText('Four kitchen table · 10 tickets collected')).toBeVisible();
  await page.getByRole('button', { name: 'Kitchen', exact: true }).click();
  for (const [index, room] of rooms.entries()) {
    await page.getByLabel('Kitchen', { exact: true }).selectOption(String(room.id));
    await expect(page.getByRole('heading', { name: 'Four kitchen table' })).toBeVisible();
    await expect(page.locator('.kitchen-order')).toContainText(foods[index].name);
    for (const other of foods.filter(f => f.id !== foods[index].id)) await expect(page.locator('.kitchen-order')).not.toContainText(other.name);
  }
  await page.getByRole('button', { name: 'Menu / take orders', exact: true }).click();
  await page.getByRole('button', { name: 'Next guest' }).click();
  await expect(page.getByRole('button', {name:'Next',exact:true})).toBeInViewport({ratio:1});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  expect(await page.evaluate(() => document.documentElement.scrollHeight <= innerHeight + 2)).toBeTruthy();
  await page.screenshot({ path: `test-results/stations-${info.project.name}.png`, fullPage: true });
});
