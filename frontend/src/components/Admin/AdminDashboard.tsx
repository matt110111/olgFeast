import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';
import { OrderStatus } from '../../types';
import { TrendingUp, Clock, DollarSign, Package, ChevronRight, CheckCircle } from 'lucide-react';

interface AdminOrder {
  id: number;
  ref_code: string;
  customer_name: string;
  status: OrderStatus;
  date_ordered: string;
  date_preparing?: string;
  date_ready?: string;
  date_complete?: string;
  total_value: number;
  order_items: Array<{
    food_item: {
      name: string;
      value: number;
    };
    quantity: number;
  }>;
}

interface AnalyticsData {
  current_status_counts: {
    pending: number;
    preparing: number;
    ready: number;
  };
  activity_stats: {
    orders_today: number;
    orders_this_week: number;
    orders_this_month: number;
  };
  timing_analytics: {
    avg_time_to_preparing: number;
    avg_time_to_ready: number;
    avg_time_to_complete: number;
    avg_total_time: number;
  };
  total_completed_orders: number;
}

const AdminDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [analyticsResponse, ordersResponse] = await Promise.all([
        apiService.get('/operations/dashboard/analytics'),
        apiService.get('/operations/orders?limit=20')
      ]);
      
      setAnalytics(analyticsResponse.data);
      setOrders(ordersResponse.data);
    } catch (error) {
      setError('Failed to load dashboard data');
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (orderId: number, newStatus: OrderStatus) => {
    try {
      await apiService.put(`/orders/${orderId}/status`, { status: newStatus });
      await fetchData(); // Refresh data
    } catch (error) {
      console.error('Error updating order status:', error);
    }
  };

  const getNextStatus = (currentStatus: OrderStatus): OrderStatus | null => {
    switch (currentStatus) {
      case OrderStatus.PENDING:
        return OrderStatus.PREPARING;
      case OrderStatus.PREPARING:
        return OrderStatus.READY;
      case OrderStatus.READY:
        return OrderStatus.COMPLETE;
      default:
        return null;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };


  const getStatusBadgeColor = (status: OrderStatus) => {
    switch (status) {
      case OrderStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800';
      case OrderStatus.PREPARING:
        return 'bg-blue-100 text-blue-800';
      case OrderStatus.READY:
        return 'bg-green-100 text-green-800';
      case OrderStatus.COMPLETE:
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

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
          onClick={fetchData}
          className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No analytics data available</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={fetchData}
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
                  <dd className="text-lg font-medium text-gray-900">
                    {analytics.current_status_counts.pending + analytics.current_status_counts.preparing + analytics.current_status_counts.ready}
                  </dd>
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
                  <dd className="text-lg font-medium text-gray-900">{analytics.activity_stats.orders_today}</dd>
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
                  <dt className="text-sm font-medium text-gray-500 truncate">Completed Orders</dt>
                  <dd className="text-lg font-medium text-gray-900">{analytics.total_completed_orders}</dd>
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
            <div className="flex justify-between items-center">
              <span className="capitalize">Pending</span>
              <span className="font-medium">{analytics.current_status_counts.pending}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="capitalize">Preparing</span>
              <span className="font-medium">{analytics.current_status_counts.preparing}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="capitalize">Ready</span>
              <span className="font-medium">{analytics.current_status_counts.ready}</span>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Activity Stats</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span>This Week</span>
              <span className="font-medium">{analytics.activity_stats.orders_this_week}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>This Month</span>
              <span className="font-medium">{analytics.activity_stats.orders_this_month}</span>
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {orders.slice(0, 10).map((order) => {
                const nextStatus = getNextStatus(order.status);
                return (
                  <tr key={order.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{order.ref_code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {order.customer_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(order.status)}`}>
                        {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${order.total_value.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(order.date_ordered)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {nextStatus && (
                        <button
                          onClick={() => handleStatusUpdate(order.id, nextStatus)}
                          className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                        >
                          <ChevronRight className="h-3 w-3 mr-1" />
                          Mark {nextStatus.charAt(0).toUpperCase() + nextStatus.slice(1)}
                        </button>
                      )}
                      {order.status === OrderStatus.COMPLETE && (
                        <span className="inline-flex items-center text-green-600">
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Complete
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          Admin Dashboard • Last updated: {new Date().toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
};

export default AdminDashboard;
