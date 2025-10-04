import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { apiService } from '../../services/api';
import { CartSummary } from '../../types';
import { CreditCard, User, CheckCircle } from 'lucide-react';

const CheckoutForm: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [cart, setCart] = useState<CartSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [customerName, setCustomerName] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    fetchCart();
  }, [isAuthenticated, navigate]);

  const fetchCart = async () => {
    try {
      const response = await apiService.getCartItems();
      setCart(response.data);
      
      if (response.data.total_items === 0) {
        navigate('/cart');
        return;
      }
    } catch (error) {
      setError('Failed to load cart');
      console.error('Error fetching cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!customerName.trim()) {
      setError('Please enter your name');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      await apiService.createOrder({ customer_name: customerName.trim() });
      navigate('/orders');
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to place order');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!cart || cart.total_items === 0) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900">Your cart is empty</h1>
        <p className="mt-2 text-gray-600">Add some items to your cart before checkout</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Checkout</h1>
        <p className="mt-2 text-gray-600">Review your order and complete your purchase</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Order Summary */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Summary</h2>
          
          <div className="space-y-3 mb-6">
            {cart.items.map((item) => (
              <div key={item.id} className="flex justify-between items-center py-2 border-b border-gray-100">
                <div>
                  <h3 className="font-medium text-gray-900">{item.food_item.name}</h3>
                  <p className="text-sm text-gray-500">{item.food_item.food_group}</p>
                </div>
                <div className="text-right">
                  <p className="font-medium">${(item.food_item.value * item.quantity).toFixed(2)}</p>
                  <p className="text-sm text-gray-500">x{item.quantity}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-gray-200 pt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span>Subtotal ({cart.total_items} items)</span>
              <span>${cart.total_value.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm text-gray-500">
              <span>Estimated tickets</span>
              <span>{cart.total_tickets}</span>
            </div>
            <div className="flex justify-between text-lg font-semibold">
              <span>Total</span>
              <span>${cart.total_value.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Checkout Form */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Customer Information</h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="customerName" className="block text-sm font-medium text-gray-700">
                Customer Name
              </label>
              <div className="mt-1 relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="customerName"
                  name="customerName"
                  type="text"
                  required
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  className="appearance-none rounded-md relative block w-full pl-10 pr-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Enter your name"
                />
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex">
                <CheckCircle className="h-5 w-5 text-blue-400 mt-0.5" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">Order Information</h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <p>• Your order will be prepared fresh</p>
                    <p>• Estimated preparation time: {cart.total_tickets * 5} minutes</p>
                    <p>• You'll receive real-time updates on order status</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex space-x-4">
              <button
                type="button"
                onClick={() => navigate('/cart')}
                className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-md text-sm font-medium hover:bg-gray-300 transition-colors"
              >
                Back to Cart
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 bg-primary-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
              >
                {submitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Placing Order...
                  </>
                ) : (
                  <>
                    <CreditCard className="h-4 w-4 mr-2" />
                    Place Order
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CheckoutForm;
