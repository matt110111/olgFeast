import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { apiService } from '../../services/api';
import { CartSummary, CartItem } from '../../types';
import { Trash2, Plus, Minus, ShoppingBag, CreditCard } from 'lucide-react';

const CartList: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [cart, setCart] = useState<CartSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      fetchCart();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const fetchCart = async () => {
    try {
      const response = await apiService.getCartItems();
      setCart(response.data);
    } catch (error) {
      setError('Failed to load cart');
      console.error('Error fetching cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuantityChange = async (cartItemId: number, change: 'increase' | 'decrease') => {
    try {
      if (change === 'increase') {
        await apiService.increaseItemQuantity(cartItemId);
      } else {
        await apiService.decreaseItemQuantity(cartItemId);
      }
      await fetchCart();
    } catch (error) {
      console.error('Error updating quantity:', error);
    }
  };

  const handleRemoveItem = async (cartItemId: number) => {
    try {
      await apiService.removeCartItem(cartItemId);
      await fetchCart();
    } catch (error) {
      console.error('Error removing item:', error);
    }
  };

  const handleClearCart = async () => {
    try {
      await apiService.clearCart();
      await fetchCart();
    } catch (error) {
      console.error('Error clearing cart:', error);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-gray-900">Shopping Cart</h1>
        <p className="mt-2 text-gray-600">Please log in to view your cart</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!cart || cart.total_items === 0) {
    return (
      <div className="text-center py-12">
        <ShoppingBag className="mx-auto h-12 w-12 text-gray-400" />
        <h1 className="mt-4 text-2xl font-bold text-gray-900">Your cart is empty</h1>
        <p className="mt-2 text-gray-600">Add some items from the menu to get started</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Shopping Cart</h1>
        <button
          onClick={handleClearCart}
          className="text-red-600 hover:text-red-800 text-sm font-medium"
        >
          Clear Cart
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="divide-y divide-gray-200">
          {(cart?.items || []).map((item) => (
            <div key={item.id} className="p-6 flex items-center justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900">
                  {item.food_item.name}
                </h3>
                <p className="text-sm text-gray-500">
                  {item.food_item.food_group} • ${item.food_item.value.toFixed(2)}
                </p>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleQuantityChange(item.id, 'decrease')}
                    className="p-1 rounded-full hover:bg-gray-100"
                  >
                    <Minus className="h-4 w-4" />
                  </button>
                  <span className="w-8 text-center font-medium">
                    {item.quantity}
                  </span>
                  <button
                    onClick={() => handleQuantityChange(item.id, 'increase')}
                    className="p-1 rounded-full hover:bg-gray-100"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>

                <div className="text-right">
                  <p className="text-lg font-medium text-gray-900">
                    ${(item.food_item.value * item.quantity).toFixed(2)}
                  </p>
                </div>

                <button
                  onClick={() => handleRemoveItem(item.id)}
                  className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-full"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-gray-50 px-6 py-4">
          <div className="flex justify-between items-center text-lg font-medium">
            <span>Total ({cart.total_items} items)</span>
            <span>${cart.total_value.toFixed(2)}</span>
          </div>
          <div className="flex justify-between items-center text-sm text-gray-500 mt-1">
            <span>Estimated tickets</span>
            <span>{cart.total_tickets}</span>
          </div>
          
          <div className="mt-4 flex space-x-3">
            <button
              onClick={() => navigate('/')}
              className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-md text-sm font-medium hover:bg-gray-300 transition-colors"
            >
              Continue Shopping
            </button>
            <button
              onClick={() => navigate('/checkout')}
              className="flex-1 bg-primary-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-primary-700 transition-colors flex items-center justify-center"
            >
              <CreditCard className="h-4 w-4 mr-2" />
              Checkout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CartList;
