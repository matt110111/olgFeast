import { apiService } from '../../services/api';
import { FoodItem, Order } from '../../types';

export interface DinnerEvent { id: number; name: string; event_date: string; closed: boolean; collect_tickets: boolean }
export interface EventRoom { id: number; event_id: number; name: string; food_item_ids: number[] }
export interface Consumable { id: number; name: string; unit: 'g' | 'ml' | 'each' }
export interface Recipe { id: number; food_item_id: number; consumable_id: number; quantity: number }
export interface EventOrder extends Order { event_id: number; room_id?: number | null; check_id?: number | null; station_number?: number | null; tickets_collected: number; awaiting_tickets?: boolean; voided_at?: string; void_reason?: string }
export interface Checkout { room_id?: number; station_number?: number; customer_name: string; items: { food_item_id: number; quantity: number }[]; checkout_key: string; tickets_collected: number }
export interface StationReceipt { id: number; station_number: number; orders: EventOrder[] }
export interface EventReportData {
  awaiting_ticket_count: number; awaiting_ticket_total: number;
  order_count: number; voided_count: number; tickets_owed: number; tickets_collected: number; voided_tickets_to_return: number;
  portions: { name: string; ordered: number; served: number; tickets: number }[];
  consumables: { id: number; name: string; unit: string; stock_added: number; estimated_used: number; estimated_remaining: number }[];
  items_without_recipes: string[];
}
export const request = <T,>(method: string, path: string, body?: unknown) => apiService.request<T>(method, path, body);
export const roomQuery = (roomId?: number) => roomId === undefined ? '' : `?room_id=${roomId}`;
export const eventApi = {
  rooms: (id: number) => request<EventRoom[]>('GET', `/events/${id}/rooms`),
  events: () => request<DinnerEvent[]>('GET', '/events'),
  foods: async (): Promise<FoodItem[]> => {
    const foods: FoodItem[] = [];
    const limit = 100;
    for (;;) {
      const { data } = await apiService.getFoodItems(foods.length, limit);
      foods.push(...data);
      if (data.length < limit) return foods;
    }
  },
  consumables: () => request<Consumable[]>('GET', '/events/setup/consumables'),
  recipes: () => request<Recipe[]>('GET', '/events/setup/recipes'),
  orders: (id: number, roomId?: number) => request<EventOrder[]>('GET', `/events/${id}/orders${roomQuery(roomId)}`),
  report: (id: number, roomId?: number) => request<EventReportData>('GET', `/events/${id}/report${roomQuery(roomId)}`),
  checkout: (id: number, data: Checkout) => request<EventOrder>('POST', `/events/${id}/checkout`, data),
  stationCheckout: (id: number, data: Checkout) => request<StationReceipt>('POST', `/events/${id}/station-checkout`, data),
};
export function errorMessage(error: unknown): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === 'string' ? detail : 'Could not reach the server. Check Wi-Fi and try again.';
}
export function newKey(): string {
  // getRandomValues works on HTTP LAN origins as well as HTTPS.
  return Array.from(crypto.getRandomValues(new Uint8Array(20)), n => n.toString(16).padStart(2, '0')).join('');
}
export type { FoodItem };
