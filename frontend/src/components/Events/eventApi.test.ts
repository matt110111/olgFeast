import { vi } from 'vitest';
import { apiService } from '../../services/api';
import { eventApi, FoodItem } from './eventApi';

vi.mock('../../services/api', () => ({ apiService: { getFoodItems: vi.fn() } }));

it('loads kitchen menu items beyond the first 100 catalog entries', async () => {
  const catalog: FoodItem[] = Array.from({ length: 114 }, (_, index) => ({
    id: index + 1, name: `Food ${index + 1}`, food_group: 'Dinner',
    value: 0, ticket: 3, is_available: true, created_at: '',
  }));
  vi.mocked(apiService.getFoodItems).mockImplementation(async (skip = 0, limit = 100) => (
    { data: catalog.slice(skip, skip + limit) } as Awaited<ReturnType<typeof apiService.getFoodItems>>
  ));
  expect(await eventApi.foods()).toEqual(catalog);
});
