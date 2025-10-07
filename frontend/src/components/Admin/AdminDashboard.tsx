import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../../services/api';
import { websocketService } from '../../services/websocket';
import { OrderStatus } from '../../types';
import { TrendingUp, Clock, DollarSign, Package, ChevronRight, CheckCircle, ChevronLeft, History, Eye } from 'lucide-react';
import WebSocketStatus from '../WebSocketStatus';
import { Link } from 'react-router-dom';

interface AdminOrder {
  id: number;
  display_id: number;
  ref_code: string;
  customer_name: string;
  status: OrderStatus;
  date_ordered: string;
  date_preparing?: string;
  date_ready?: string;
  date_complete?: string;
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
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalOrders, setTotalOrders] = useState(0);

  const fetchData = useCallback(async (page: number = 1) => {
    try {
      setLoading(true);
      const [analyticsResponse, ordersResponse] = await Promise.all([
        apiService.get('/operations/dashboard/analytics'),
        apiService.get(`/operations/orders?page=${page}&per_page=10`)
      ]);

      setAnalytics(analyticsResponse.data);
      
      // Handle paginated response
      if (ordersResponse.data.orders) {
        setOrders(ordersResponse.data.orders);
        setTotalPages(ordersResponse.data.total_pages);
        setTotalOrders(ordersResponse.data.total);
      } else {
        // Fallback for non-paginated response
        setOrders(ordersResponse.data);
      }
    } catch (error) {
      setError('Failed to load dashboard data');
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const setupWebSocket = useCallback(() => {
    try {
      // Connect to admin dashboard WebSocket
      const ws = websocketService.connectAdminDashboard();
      
      if (!ws) {
        console.error('Failed to connect to admin WebSocket');
        return;
      }

      // Subscribe to analytics updates
      websocketService.subscribe('/ws/admin/dashboard', 'dashboard_analytics', (message) => {
        try {
          if (message.type === 'dashboard_analytics' && message.data) {
            setAnalytics(message.data);
          }
        } catch (error) {
          console.error('Error processing analytics update:', error);
          // Fallback to REST API
          fetchData();
        }
      });

      // Subscribe to orders updates
      websocketService.subscribe('/ws/admin/dashboard', 'all_orders_update', (message) => {
        try {
          if (message.type === 'all_orders_update' && message.data) {
            setOrders(message.data.orders || []);
          }
        } catch (error) {
          console.error('Error processing orders update:', error);
          // Fallback to REST API
          fetchData();
        }
      });

      // Subscribe to order status changes
      websocketService.subscribe('/ws/admin/dashboard', 'order_status_change', (message) => {
        try {
          if (message.type === 'order_status_change') {
            // Request updated data instead of full refresh
            websocketService.requestAnalytics();
            websocketService.requestOrders();
          }
        } catch (error) {
          console.error('Error processing order status change:', error);
          fetchData();
        }
      });

      // Subscribe to new orders
      websocketService.subscribe('/ws/admin/dashboard', 'new_order', (message) => {
        try {
          if (message.type === 'new_order') {
            // Request updated data instead of full refresh
            websocketService.requestAnalytics();
            websocketService.requestOrders();
          }
        } catch (error) {
          console.error('Error processing new order:', error);
          fetchData();
        }
      });

      // Request initial data via WebSocket
      websocketService.requestAnalytics();
      websocketService.requestOrders();
      
    } catch (error) {
      console.error('Failed to setup WebSocket:', error);
      // Fallback to REST API only
      fetchData();
    }
  }, [fetchData]);

  useEffect(() => {
    // Initial data fetch
    fetchData(currentPage);

    // Connect to WebSocket for real-time updates
    setupWebSocket();

    return () => {
      websocketService.disconnect('/ws/admin/dashboard');
    };
  }, [currentPage, fetchData, setupWebSocket]);

  const handleStatusUpdate = async (orderId: number, newStatus: OrderStatus) => {
    try {
      await apiService.put(`/orders/${orderId}/status`, { status: newStatus });
      // WebSocket will automatically update the UI - no manual refresh needed!
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

  const calculateOrderTotal = (order: AdminOrder): number => {
    if (!order.order_items || !Array.isArray(order.order_items)) {
      return 0;
    }
    return order.order_items.reduce((total, item) => {
      return total + (item.food_item.value * item.quantity);
    }, 0);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const year = String(date.getFullYear()).slice(-2);
    const hours = date.getHours();
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    return `${month}/${day}/${year} ${displayHours}:${minutes}:${seconds} ${ampm}`;
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
          onClick={() => fetchData(currentPage)}
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
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <WebSocketStatus endpoint="/ws/admin/dashboard" />
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => fetchData(currentPage)}
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
                    {analytics?.current_status_counts ? 
                      analytics.current_status_counts.pending + analytics.current_status_counts.preparing + analytics.current_status_counts.ready 
                      : 0}
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
                  <dd className="text-lg font-medium text-gray-900">{analytics?.activity_stats?.orders_today ?? 0}</dd>
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
                  <dd className="text-lg font-medium text-gray-900">{analytics?.timing_analytics?.avg_total_time ?? 0}min</dd>
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
              <span className="font-medium">{analytics?.current_status_counts?.pending ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="capitalize">Preparing</span>
              <span className="font-medium">{analytics?.current_status_counts?.preparing ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="capitalize">Ready</span>
              <span className="font-medium">{analytics?.current_status_counts?.ready ?? 0}</span>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Activity Stats</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span>This Week</span>
              <span className="font-medium">{analytics?.activity_stats?.orders_this_week ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>This Month</span>
              <span className="font-medium">{analytics?.activity_stats?.orders_this_month ?? 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Completed Orders</span>
              <span className="font-medium">{analytics?.total_completed_orders ?? 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Recent Orders</h3>
              <p className="text-sm text-gray-500">Showing {orders.length} of {totalOrders} orders</p>
            </div>
            <Link
              to="/admin/orders"
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <History className="h-4 w-4 mr-2" />
              View All Orders
            </Link>
          </div>
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
              {(orders || []).map((order) => {
                const nextStatus = getNextStatus(order.status);
                return (
                  <tr key={order.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{order.display_id} • {order.ref_code}
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
                      ${calculateOrderTotal(order).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(order.date_ordered)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex flex-col space-y-1">
                        <Link
                          to={`/admin/orders/${order.id}`}
                          className="inline-flex items-center px-2 py-1 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          View Details
                        </Link>
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
                          <span className="inline-flex items-center text-green-600 text-xs">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Complete
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing{' '}
                  <span className="font-medium">{(currentPage - 1) * 10 + 1}</span>
                  {' '}to{' '}
                  <span className="font-medium">
                    {Math.min(currentPage * 10, totalOrders)}
                  </span>
                  {' '}of{' '}
                  <span className="font-medium">{totalOrders}</span>
                  {' '}results
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  
                  {/* Page numbers */}
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                    if (pageNum > totalPages) return null;
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          pageNum === currentPage
                            ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
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
