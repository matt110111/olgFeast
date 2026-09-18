import { test, expect } from '@playwright/test';
import { submitLogin } from './login';

test('fourteen-item menu and a large check fit without scrolling the page', async ({page, request}, info) => {
  const api = process.env.E2E_API_URL || 'http://127.0.0.1:8002';
  const password = process.env.E2E_ADMIN_PASSWORD!;
  const login = await request.post(`${api}/api/v1/auth/login`, {form:{username:'admin',password}});
  const headers = {Authorization:`Bearer ${(await login.json()).access_token}`};
  async function write(method:'post'|'put', path:string, data:unknown) {
    const r=await request[method](`${api}/api/v1${path}`,{headers,data});
    expect(r.ok(),await r.text()).toBeTruthy(); return r.json();
  }
  const event=await write('post','/events',{name:`iPad menu ${Date.now()}`,event_date:'2026-09-26'});
  const names=['Wings','Grilled Salmon','Beef Steak','Sausage & Peppers Sandwich','Chicken Alfredo','Garlic Bread','Coffee','Vegetarian Pasta','Caesar Salad','Chocolate Cake','Tiramisu','Ice Cream','Fresh Juice','Soft Drinks'];
  const roomNames=['Fried','Grilled','Cooked 1','Cooked 2'];
  const assignment=[0,1,1,1,2,2,2,3,3,3,3,3,3,3];
  const ids:number[][]=[[],[],[],[]];
  for(const [i,name] of names.entries()) {
    const f=await write('post','/menu/items',{name,food_group:roomNames[assignment[i]],ticket:3,value:0,is_available:true});
    ids[assignment[i]].push(f.id);
  }
  for(const [i,name] of roomNames.entries()) {
    const room=await write('post',`/events/${event.id}/rooms`,{name});
    await write('put',`/events/${event.id}/rooms/${room.id}/menu`,{food_item_ids:ids[i]});
  }
  await page.goto('/login');
  await page.getByLabel('Username',{exact:true}).fill('admin');
  await page.getByLabel('Password',{exact:true}).fill(password);
  await submitLogin(page);
  await expect(page).toHaveURL(/\/event$/);
  await page.getByLabel('Current event').selectOption(String(event.id));
  await expect(page.locator('.food-tile').first()).toBeVisible();
  let added = 0;
  for(let pageNumber=0;pageNumber<14;pageNumber++) {
    const tiles=page.locator('.food-tile');
    const count=await tiles.count();
    expect(count).toBeGreaterThan(0);
    for(let i=0;i<count;i++) {
      await expect(tiles.nth(i)).toBeInViewport({ratio:1});
      expect(await tiles.nth(i).evaluate(el => el.scrollHeight <= el.clientHeight + 1)).toBeTruthy();
      await tiles.nth(i).click();
      added++;
    }
    const next = page.getByRole('button',{name:'Next',exact:true});
    if(await next.isDisabled()) break;
    await next.click();
  }
  expect(added).toBe(14);
  const check=page.getByRole('button',{name:'Check order · 42 tickets'});
  await expect(check).toBeInViewport({ratio:1});
  expect(await page.evaluate(()=>document.documentElement.scrollHeight <= innerHeight+2)).toBeTruthy();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.screenshot({path:`test-results/full-menu-${info.project.name}.png`});
  await check.click();
  await expect(page.getByLabel('I collected 42 tickets')).toBeInViewport({ratio:1});
  await expect(page.getByRole('button',{name:'Send to kitchen',exact:true})).toBeInViewport({ratio:1});
  expect(await page.evaluate(()=>document.documentElement.scrollHeight <= innerHeight+2)).toBeTruthy();
  await page.screenshot({path:`test-results/check-screen-${info.project.name}.png`});
  await page.getByLabel('I collected 42 tickets').check();
  await page.getByRole('button',{name:'Back to menu'}).click();
  await page.getByRole('button',{name:'Check order · 42 tickets'}).click();
  await expect(page.getByLabel('I collected 42 tickets')).not.toBeChecked();
});
