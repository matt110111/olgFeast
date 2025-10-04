import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../../services/api';
import { websocketService } from '../../services/websocket';
import { OrderStatus } from '../../types';
import { Clock, CheckCircle, Package, Truck } from 'lucide-react';
import WebSocketStatus from '../WebSocketStatus';

interface KitchenOrder {
  id: number;
  display_id: number;
  ref_code: string;
  customer_name: string;
  status: OrderStatus;
  date_ordered: string;
  date_preparing?: string;
  date_ready?: string;
  order_items: Array<{
    food_item: {
      name: string;
      value: number;
      ticket: number;
    };
    quantity: number;
  }>;
}

const KitchenDisplay: React.FC = () => {
  const [orders, setOrders] = useState<{
    pending: KitchenOrder[];
    preparing: KitchenOrder[];
    ready: KitchenOrder[];
  }>({
    pending: [],
    preparing: [],
    ready: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchOrders = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      
      // Check if we have a valid token
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in.');
      }
      
      console.log('Fetching kitchen orders with token:', token ? 'Present' : 'Missing');
      
      const [pendingResponse, preparingResponse, readyResponse] = await Promise.all([
        apiService.get('/operations/orders/pending'),
        apiService.get('/operations/orders/preparing'),
        apiService.get('/operations/orders/ready')
      ]);

      setOrders({
        pending: pendingResponse.data || [],
        preparing: preparingResponse.data || [],
        ready: readyResponse.data || []
      });
    } catch (error: any) {
      console.error('Error fetching kitchen orders:', error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        setError('Authentication failed. Please log in again.');
      } else if (error.response?.status === 422) {
        setError('Invalid request. Please ensure you are logged in as a staff member.');
      } else {
        setError(`Failed to load kitchen orders: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const setupWebSocket = useCallback(() => {
    try {
      // Connect to kitchen display WebSocket
      const ws = websocketService.connectKitchenDisplay();
      
      if (!ws) {
        console.error('Failed to connect to kitchen WebSocket');
        return;
      }

      // Subscribe to kitchen updates
      websocketService.subscribe('/ws/kitchen/display', 'kitchen_update', (message) => {
        try {
          if (message.type === 'kitchen_update' && message.data) {
            setOrders({
              pending: message.data.pending_orders || [],
              preparing: message.data.preparing_orders || [],
              ready: message.data.ready_orders || []
            });
          }
        } catch (error) {
          console.error('Error processing kitchen update:', error);
          // Fallback to REST API
          fetchOrders();
        }
      });

      // Subscribe to order status changes
      websocketService.subscribe('/ws/kitchen/display', 'order_status_change', (message) => {
        try {
          if (message.type === 'order_status_change') {
            // Request updated kitchen state instead of full refresh
            websocketService.requestKitchenUpdate();
          }
        } catch (error) {
          console.error('Error processing order status change:', error);
          fetchOrders();
        }
      });

      // Subscribe to new orders
      websocketService.subscribe('/ws/kitchen/display', 'new_order', (message) => {
        try {
          if (message.type === 'new_order') {
            // Request updated kitchen state instead of full refresh
            websocketService.requestKitchenUpdate();
          }
        } catch (error) {
          console.error('Error processing new order:', error);
          fetchOrders();
        }
      });

      // Request initial update via WebSocket
      websocketService.requestKitchenUpdate();
      
    } catch (error) {
      console.error('Failed to setup WebSocket:', error);
      // Fallback to REST API only
      fetchOrders();
    }
  }, []); // Remove fetchOrders dependency to prevent infinite re-renders

  useEffect(() => {
    // Initial data fetch
    fetchOrders();

    // Connect to WebSocket for real-time updates
    setupWebSocket();

    return () => {
      websocketService.disconnect('/ws/kitchen/display');
    };
  }, [fetchOrders, setupWebSocket]);


  const getStatusIcon = (status: OrderStatus) => {
    switch (status) {
      case OrderStatus.PENDING:
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case OrderStatus.PREPARING:
        return <Package className="h-5 w-5 text-blue-500" />;
      case OrderStatus.READY:
        return <Truck className="h-5 w-5 text-green-500" />;
      case OrderStatus.COMPLETE:
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateOrderTotal = (order: KitchenOrder): number => {
    if (!order.order_items || !Array.isArray(order.order_items)) {
      return 0;
    }
    return order.order_items.reduce((total, item) => {
      return total + (item.food_item.value * item.quantity);
    }, 0);
  };

  const calculateTotalTickets = (order: KitchenOrder): number => {
    if (!order.order_items || !Array.isArray(order.order_items)) {
      return 0;
    }
    return order.order_items.reduce((total, item) => {
      return total + (item.food_item.ticket * item.quantity);
    }, 0);
  };

  const OrderCard: React.FC<{ order: KitchenOrder; status: OrderStatus }> = ({ order, status }) => {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-l-primary-500">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            {getStatusIcon(status)}
            <span className="text-lg font-semibold text-gray-800 mb-3">{order.customer_name}</span>

          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">{formatTime(order.date_ordered)}</p>
            <p className="font-medium">${calculateOrderTotal(order).toFixed(2)}</p>
          </div>
        </div>
        
        <p className="font-semibold text-sm">#{order.display_id}</p>
        
        <div className="space-y-1 mb-3">
          {(order.order_items || []).map((item, index) => (
            <div key={index} className="flex justify-between text-sm">
              <span>{item.food_item.name}</span>
              <span className="font-medium">x{item.quantity}</span>
            </div>
          ))}
        </div>
        
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>{calculateTotalTickets(order)} tickets</span>
          <span>{(order.order_items || []).length} items</span>
        </div>
      </div>
    );
  };

  const Section: React.FC<{ title: string; orders: KitchenOrder[]; status: OrderStatus; color: string }> = ({ 
    title, 
    orders, 
    status, 
    color 
  }) => (
    <div className="flex-1">
      <div className={`${color} text-white px-4 py-2 rounded-t-lg`}>
        <h2 className="text-lg font-semibold">{title} ({(orders || []).length})</h2>
      </div>
      <div className="bg-gray-50 rounded-b-lg p-4 min-h-[400px]">
        <div className="space-y-3">
          {(orders || []).length === 0 ? (
            <p className="text-gray-500 text-center py-8">No orders</p>
          ) : (
            (orders || []).map((order) => (
              <OrderCard key={order.id} order={order} status={status} />
            ))
          )}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <button
          onClick={fetchOrders}
          className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-900">Kitchen Display</h1>
          <WebSocketStatus endpoint="/ws/kitchen/display" />
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={fetchOrders}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm"
          >
            Refresh
          </button>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-sm text-gray-600">
              Live Data
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Section
          title="Pending Orders"
          orders={orders.pending}
          status={OrderStatus.PENDING}
          color="bg-yellow-500"
        />
        <Section
          title="Preparing"
          orders={orders.preparing}
          status={OrderStatus.PREPARING}
          color="bg-blue-500"
        />
        <Section
          title="Ready for Pickup"
          orders={orders.ready}
          status={OrderStatus.READY}
          color="bg-green-500"
        />
      </div>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          Kitchen Display • Last updated: {new Date().toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
};

export default KitchenDisplay;
