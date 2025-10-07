import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService } from '../../services/api';
import { OrderStatus } from '../../types';
import { 
  ArrowLeft, 
  Clock, 
  Calendar, 
  Package, 
  DollarSign, 
  CheckCircle,
  AlertCircle,
  ChefHat,
  Truck
} from 'lucide-react';

interface OrderItem {
  id: number;
  food_item: {
    id: number;
    name: string;
    value: number;
    ticket: number;
    food_group: string;
  };
  quantity: number;
}

interface Order {
  id: number;
  display_id: number;
  ref_code: string;
  customer_name: string;
  status: OrderStatus;
  date_ordered: string;
  date_preparing?: string;
  date_ready?: string;
  date_complete?: string;
  last_status_change: string;
  order_items: OrderItem[];
  user_id: number;
}

const OrderDetail: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchOrderDetails = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiService.get(`/operations/orders/${orderId}`);
      setOrder(response.data);
    } catch (error) {
      setError('Failed to load order details');
      console.error('Error fetching order details:', error);
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (orderId) {
      fetchOrderDetails();
    }
  }, [orderId, fetchOrderDetails]);

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

  const formatDuration = (startDate: string, endDate?: string) => {
    if (!endDate) return 'In Progress';
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffMs = end.getTime() - start.getTime();
    const diffMins = Math.round(diffMs / (1000 * 60));
    
    if (diffMins < 60) {
      return `${diffMins} minutes`;
    } else {
      const hours = Math.floor(diffMins / 60);
      const mins = diffMins % 60;
      return `${hours} hours ${mins} minutes`;
    }
  };

  const calculateOrderTotal = () => {
    if (!order?.order_items) return 0;
    return order.order_items.reduce((total, item) => {
      return total + (item.food_item.value * item.quantity);
    }, 0);
  };

  const calculateTotalTickets = () => {
    if (!order?.order_items) return 0;
    return order.order_items.reduce((total, item) => {
      return total + (item.food_item.ticket * item.quantity);
    }, 0);
  };

  const getStatusIcon = (status: OrderStatus) => {
    switch (status) {
      case OrderStatus.PENDING:
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case OrderStatus.PREPARING:
        return <ChefHat className="h-5 w-5 text-blue-500" />;
      case OrderStatus.READY:
        return <Truck className="h-5 w-5 text-green-500" />;
      case OrderStatus.COMPLETE:
        return <CheckCircle className="h-5 w-5 text-gray-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: OrderStatus) => {
    switch (status) {
      case OrderStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case OrderStatus.PREPARING:
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case OrderStatus.READY:
        return 'bg-green-100 text-green-800 border-green-200';
      case OrderStatus.COMPLETE:
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                {error || 'Order not found'}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={() => navigate(-1)}
              className="mr-4 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Order Details</h1>
              <p className="mt-2 text-gray-600">Order #{order.display_id} • Ref: {order.ref_code}</p>
            </div>
          </div>
          <div className={`inline-flex items-center px-4 py-2 border rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
            {getStatusIcon(order.status)}
            <span className="ml-2">{order.status.charAt(0).toUpperCase() + order.status.slice(1)}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Order Information */}
        <div className="lg:col-span-3 space-y-6">
          {/* Order Summary */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Order Summary</h3>
            </div>
            <div className="p-6">
              <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Order ID</dt>
                  <dd className="mt-1 text-sm text-gray-900">{order.id}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Reference Code</dt>
                  <dd className="mt-1 text-sm text-gray-900">#{order.ref_code}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Customer</dt>
                  <dd className="mt-1 text-sm text-gray-900">{order.customer_name}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Total Items</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {order.order_items.reduce((total, item) => total + item.quantity, 0)} items
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Order Items */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Order Items</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Item
                    </th>
                    <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Qty
                    </th>
                    <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Unit Price
                    </th>
                    <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                    <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tickets
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {order.order_items.map((item) => (
                    <tr key={item.id}>
                      <td className="px-3 py-4">
                        <div className="flex items-center">
                          <Package className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0" />
                          <div className="text-sm font-medium text-gray-900 truncate">
                            {item.food_item.name}
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-4 text-sm text-gray-500 min-w-0">
                        <div className="truncate">{item.food_item.food_group}</div>
                      </td>
                      <td className="px-3 py-4 text-sm text-gray-900 text-center min-w-0">
                        {item.quantity}
                      </td>
                      <td className="px-3 py-4 text-sm text-gray-900 text-right min-w-0">
                        ${item.food_item.value.toFixed(2)}
                      </td>
                      <td className="px-3 py-4 text-sm text-gray-900 text-right min-w-0">
                        ${(item.food_item.value * item.quantity).toFixed(2)}
                      </td>
                      <td className="px-3 py-4 text-sm text-gray-900 text-center min-w-0">
                        {item.food_item.ticket * item.quantity}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-50">
                  <tr>
                    <td colSpan={4} className="px-3 py-4 text-right text-sm font-medium text-gray-500">
                      Order Total:
                    </td>
                    <td className="px-3 py-4 text-right text-sm font-medium text-gray-900">
                      ${calculateOrderTotal().toFixed(2)}
                    </td>
                    <td className="px-3 py-4 text-center text-sm font-medium text-gray-900">
                      {calculateTotalTickets()} tickets
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>

        {/* Timeline and Status */}
        <div className="lg:col-span-2 space-y-6">
          {/* Order Timeline */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Order Timeline</h3>
            </div>
            <div className="p-6 pb-8">
              <div className="flow-root">
                <ul className="space-y-4">
                  {/* Ordered */}
                  <li>
                    <div className="relative pb-8">
                      <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                      <div className="relative flex space-x-3">
                        <div>
                          <span className="h-8 w-8 rounded-full bg-green-500 flex items-center justify-center ring-8 ring-white">
                            <CheckCircle className="h-5 w-5 text-white" />
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 pt-1.5">
                          <div>
                            <p className="text-sm text-gray-500">Order Placed</p>
                            <p className="text-xs text-gray-400">{formatDate(order.date_ordered)}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>

                  {/* Preparing */}
                  {order.date_preparing && (
                    <li>
                      <div className="relative pb-8">
                        <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                        <div className="relative flex space-x-3">
                          <div>
                            <span className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center ring-8 ring-white">
                              <ChefHat className="h-5 w-5 text-white" />
                            </span>
                          </div>
                          <div className="min-w-0 flex-1 pt-1.5">
                            <div>
                              <p className="text-sm text-gray-500">Started Preparing</p>
                              <p className="text-xs text-gray-400">{formatDate(order.date_preparing)}</p>
                              <p className="text-xs text-blue-600">
                                {formatDuration(order.date_ordered, order.date_preparing)}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  )}

                  {/* Ready */}
                  {order.date_ready && (
                    <li>
                      <div className="relative pb-8">
                        <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                        <div className="relative flex space-x-3">
                          <div>
                            <span className="h-8 w-8 rounded-full bg-green-500 flex items-center justify-center ring-8 ring-white">
                              <Truck className="h-5 w-5 text-white" />
                            </span>
                          </div>
                          <div className="min-w-0 flex-1 pt-1.5">
                            <div>
                              <p className="text-sm text-gray-500">Ready for Pickup</p>
                              <p className="text-xs text-gray-400">{formatDate(order.date_ready)}</p>
                              <p className="text-xs text-green-600">
                                {formatDuration(order.date_preparing || order.date_ordered, order.date_ready)}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  )}

                  {/* Complete */}
                  {order.date_complete && (
                    <li>
                      <div className="relative pb-4">
                        <div className="relative flex space-x-3">
                          <div>
                            <span className="h-8 w-8 rounded-full bg-gray-500 flex items-center justify-center ring-8 ring-white">
                              <CheckCircle className="h-5 w-5 text-white" />
                            </span>
                          </div>
                          <div className="min-w-0 flex-1 pt-1.5">
                            <div>
                              <p className="text-sm text-gray-500">Order Completed</p>
                              <p className="text-xs text-gray-400">{formatDate(order.date_complete)}</p>
                              <p className="text-xs text-gray-600">
                                Total: {formatDuration(order.date_ordered, order.date_complete)}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  )}
                </ul>
              </div>
            </div>
          </div>

          {/* Order Stats */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Order Statistics</h3>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <DollarSign className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-sm text-gray-500">Total Value</span>
                </div>
                <span className="text-sm font-medium text-gray-900">
                  ${calculateOrderTotal().toFixed(2)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Package className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-sm text-gray-500">Total Items</span>
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {order.order_items.reduce((total, item) => total + item.quantity, 0)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Clock className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-sm text-gray-500">Processing Time</span>
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {order.date_complete 
                    ? formatDuration(order.date_ordered, order.date_complete)
                    : 'In Progress'
                  }
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Calendar className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-sm text-gray-500">Last Updated</span>
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {formatDate(order.last_status_change)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderDetail;
