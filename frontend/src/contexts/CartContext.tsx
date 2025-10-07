import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { apiService } from '../services/api';
import { CartSummary } from '../types';

interface CartContextType {
  cart: CartSummary | null;
  cartItemCount: number;
  isLoading: boolean;
  error: string | null;
  addToCart: (foodItemId: number, quantity?: number) => Promise<void>;
  removeFromCart: (cartItemId: number) => Promise<void>;
  updateQuantity: (cartItemId: number, quantity: number) => Promise<void>;
  clearCart: () => Promise<void>;
  refreshCart: () => Promise<void>;
  recentlyAdded: number | null; // ID of recently added item
  setRecentlyAdded: (id: number | null) => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const useCart = () => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

interface CartProviderProps {
  children: ReactNode;
}

export const CartProvider: React.FC<CartProviderProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [cart, setCart] = useState<CartSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentlyAdded, setRecentlyAdded] = useState<number | null>(null);

  const cartItemCount = cart?.total_items || 0;

  const fetchCart = useCallback(async () => {
    if (!isAuthenticated) {
      setCart(null);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await apiService.getCartItems();
      setCart(response.data);
    } catch (err) {
      setError('Failed to load cart');
      console.error('Error fetching cart:', err);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  const addToCart = useCallback(async (foodItemId: number, quantity: number = 1) => {
    try {
      setError(null);
      await apiService.addToCart({
        food_item_id: foodItemId,
        quantity,
      });
      
      // Show recently added indicator
      setRecentlyAdded(foodItemId);
      setTimeout(() => setRecentlyAdded(null), 2000);
      
      // Refresh cart
      await fetchCart();
    } catch (err) {
      setError('Failed to add item to cart');
      console.error('Error adding to cart:', err);
      throw err;
    }
  }, [fetchCart]);

  const removeFromCart = useCallback(async (cartItemId: number) => {
    try {
      setError(null);
      await apiService.removeCartItem(cartItemId);
      await fetchCart();
    } catch (err) {
      setError('Failed to remove item from cart');
      console.error('Error removing from cart:', err);
      throw err;
    }
  }, [fetchCart]);

  const updateQuantity = useCallback(async (cartItemId: number, quantity: number) => {
    try {
      setError(null);
      await apiService.updateCartItem(cartItemId, { quantity });
      await fetchCart();
    } catch (err) {
      setError('Failed to update item quantity');
      console.error('Error updating quantity:', err);
      throw err;
    }
  }, [fetchCart]);

  const clearCart = useCallback(async () => {
    try {
      setError(null);
      await apiService.clearCart();
      await fetchCart();
    } catch (err) {
      setError('Failed to clear cart');
      console.error('Error clearing cart:', err);
      throw err;
    }
  }, [fetchCart]);

  const refreshCart = useCallback(async () => {
    await fetchCart();
  }, [fetchCart]);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const value: CartContextType = {
    cart,
    cartItemCount,
    isLoading,
    error,
    addToCart,
    removeFromCart,
    updateQuantity,
    clearCart,
    refreshCart,
    recentlyAdded,
    setRecentlyAdded,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};
