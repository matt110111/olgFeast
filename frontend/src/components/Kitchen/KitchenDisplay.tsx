import React, { useState, useEffect } from 'react';
import { websocketService } from '../../services/websocket';
import { KitchenUpdateMessage, OrderStatus } from '../../types';
import { Clock, CheckCircle, Package, Truck } from 'lucide-react';

interface KitchenOrder {
  id: number;
  ref_code: string;
  customer_name: string;
  status: OrderStatus;
  date_ordered: string;
  date_preparing?: string;
  date_ready?: string;
  items: Array<{
    name: string;
    quantity: number;
  }>;
  total_value: number;
  total_tickets: number;
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
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Connect to kitchen display WebSocket
    websocketService.connectKitchenDisplay();
    setConnected(true);

    // Subscribe to kitchen updates
    websocketService.subscribe('/ws/kitchen/display', 'kitchen_update', (message) => {
      if (message.type === 'kitchen_update') {
        const data = message.data as KitchenUpdateMessage;
        setOrders({
          pending: data.pending_orders || [],
          preparing: data.preparing_orders || [],
          ready: data.ready_orders || []
        });
      }
    });

    // Request initial update
    websocketService.requestKitchenUpdate();

    // Cleanup on unmount
    return () => {
      websocketService.disconnect('/ws/kitchen/display');
    };
  }, []);

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

  const OrderCard: React.FC<{ order: KitchenOrder; status: OrderStatus }> = ({ order, status }) => (
    <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-l-primary-500">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          {getStatusIcon(status)}
          <span className="font-semibold text-lg">#{order.ref_code}</span>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">{formatTime(order.date_ordered)}</p>
          <p className="font-medium">${order.total_value.toFixed(2)}</p>
        </div>
      </div>
      
      <p className="text-sm text-gray-600 mb-3">{order.customer_name}</p>
      
      <div className="space-y-1 mb-3">
        {order.items.map((item, index) => (
          <div key={index} className="flex justify-between text-sm">
            <span>{item.name}</span>
            <span className="font-medium">x{item.quantity}</span>
          </div>
        ))}
      </div>
      
      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>{order.total_tickets} tickets</span>
        <span>{order.items.length} items</span>
      </div>
    </div>
  );

  const Section: React.FC<{ title: string; orders: KitchenOrder[]; status: OrderStatus; color: string }> = ({ 
    title, 
    orders, 
    status, 
    color 
  }) => (
    <div className="flex-1">
      <div className={`${color} text-white px-4 py-2 rounded-t-lg`}>
        <h2 className="text-lg font-semibold">{title} ({orders.length})</h2>
      </div>
      <div className="bg-gray-50 rounded-b-lg p-4 min-h-[400px]">
        <div className="space-y-3">
          {orders.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No orders</p>
          ) : (
            orders.map((order) => (
              <OrderCard key={order.id} order={order} status={status} />
            ))
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Kitchen Display</h1>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
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
          Real-time updates • Last updated: {new Date().toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
};

export default KitchenDisplay;
