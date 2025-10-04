import React, { useState, useEffect } from 'react';
import { websocketService } from '../../services/websocket';
import { AdminDashboardAnalytics } from '../../types';
import { BarChart3, TrendingUp, Clock, Users, DollarSign, Package } from 'lucide-react';

interface AdminOrder {
  id: number;
  ref_code: string;
  customer_name: string;
  status: string;
  date_ordered: string;
  date_preparing?: string;
  date_ready?: string;
  date_complete?: string;
  total_value: number;
  order_items: Array<{
    food_item_name: string;
    quantity: number;
  }>;
}

const AdminDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AdminDashboardAnalytics | null>(null);
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Connect to admin dashboard WebSocket
    websocketService.connectAdminDashboard();
    setConnected(true);

    // Subscribe to analytics updates
    websocketService.subscribe('/ws/admin/dashboard', 'dashboard_analytics', (message) => {
      if (message.type === 'dashboard_analytics') {
        setAnalytics(message.data);
      }
    });

    // Subscribe to orders updates
    websocketService.subscribe('/ws/admin/dashboard', 'all_orders_update', (message) => {
      if (message.type === 'all_orders_update') {
        setOrders(message.data.orders || []);
      }
    });

    // Request initial data
    websocketService.requestAnalytics();
    websocketService.requestOrders();

    // Cleanup on unmount
    return () => {
      websocketService.disconnect('/ws/admin/dashboard');
    };
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return 'text-yellow-600';
      case 'preparing':
        return 'text-blue-600';
      case 'ready':
        return 'text-green-600';
      case 'complete':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  if (!analytics) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">
            {connected ? 'Live Updates' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Package className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Orders</dt>
                  <dd className="text-lg font-medium text-gray-900">{analytics.total_orders}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Today's Orders</dt>
                  <dd className="text-lg font-medium text-gray-900">{analytics.orders_today}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DollarSign className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Revenue</dt>
                  <dd className="text-lg font-medium text-gray-900">${analytics.total_revenue.toFixed(2)}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Clock className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Avg. Time</dt>
                  <dd className="text-lg font-medium text-gray-900">{analytics.timing_analytics.avg_total_time}min</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Order Status Overview</h3>
          <div className="space-y-3">
            {Object.entries(analytics.status_counts).map(([status, count]) => (
              <div key={status} className="flex justify-between items-center">
                <span className="capitalize">{status}</span>
                <span className="font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Activity Stats</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span>This Week</span>
              <span className="font-medium">{analytics.orders_this_week}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>This Month</span>
              <span className="font-medium">{analytics.orders_this_month}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Completed Orders</span>
              <span className="font-medium">{analytics.total_completed_orders}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Recent Orders</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Order
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Customer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Time
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {orders.slice(0, 10).map((order) => (
                <tr key={order.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    #{order.ref_code}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {order.customer_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={getStatusColor(order.status)}>
                      {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${order.total_value.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(order.date_ordered)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          Real-time analytics • Last updated: {new Date().toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
};

export default AdminDashboard;
