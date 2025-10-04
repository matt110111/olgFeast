import React, { useState, useEffect, memo, useCallback } from 'react';
import { FoodItem, FoodItemGroup } from '../../types';
import { apiService } from '../../services/api';
import { useCart } from '../../contexts/CartContext';
import { ShoppingCart, DollarSign, Clock, Check } from 'lucide-react';

const MenuList: React.FC = memo(() => {
  const { addToCart, recentlyAdded, isLoading: cartLoading } = useCart();
  const [foodGroups, setFoodGroups] = useState<FoodItemGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [addingToCart, setAddingToCart] = useState<number | null>(null);

  useEffect(() => {
    fetchMenuItems();
  }, []);

  const fetchMenuItems = async () => {
    try {
      const response = await apiService.getFoodGroups();
      setFoodGroups(response.data);
    } catch (error) {
      setError('Failed to load menu items');
      console.error('Error fetching menu items:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = useCallback(async (foodItem: FoodItem, event?: React.MouseEvent) => {
    // Prevent event bubbling if clicking the add button specifically
    if (event) {
      event.stopPropagation();
    }
    
    try {
      setAddingToCart(foodItem.id);
      await addToCart(foodItem.id, 1);
      console.log(`Added ${foodItem.name} to cart`);
    } catch (error) {
      console.error('Failed to add item to cart:', error);
    } finally {
      setAddingToCart(null);
    }
  }, [addToCart]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="sr-only">Loading menu...</span>
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

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Our Menu</h1>
        <p className="mt-2 text-gray-600">
          Discover our delicious selection of fresh, high-quality dishes
        </p>
      </div>

      {foodGroups.map((group) => (
        <div key={group.group} className="space-y-4">
          <h2 className="text-2xl font-semibold text-gray-800 border-b border-gray-200 pb-2">
            {group.group}
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {group.items.map((item) => {
              const isAdding = addingToCart === item.id;
              const wasRecentlyAdded = recentlyAdded === item.id;
              
              return (
                <div
                  key={item.id}
                  onClick={() => handleAddToCart(item)}
                  className={`
                    bg-white rounded-lg shadow-md overflow-hidden 
                    cursor-pointer transform transition-all duration-200 ease-in-out
                    hover:shadow-xl hover:scale-105 hover:-translate-y-1
                    ${wasRecentlyAdded ? 'ring-2 ring-green-400 ring-opacity-75 shadow-green-200' : ''}
                    ${isAdding ? 'opacity-75 scale-95' : ''}
                    active:scale-95
                  `}
                >
                  <div className="p-6 relative">
                    {/* Success overlay */}
                    {wasRecentlyAdded && (
                      <div className="absolute inset-0 bg-green-50 bg-opacity-90 flex items-center justify-center rounded-lg animate-pulse">
                        <div className="flex items-center space-x-2 text-green-600 font-semibold">
                          <Check className="h-6 w-6" />
                          <span>Added to Cart!</span>
                        </div>
                      </div>
                    )}
                    
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {item.name}
                      </h3>
                      <span className="bg-primary-100 text-primary-800 text-xs font-medium px-2 py-1 rounded-full">
                        {item.ticket} ticket{item.ticket !== 1 ? 's' : ''}
                      </span>
                    </div>
                    
                    {item.description && (
                      <p className="text-gray-600 text-sm mb-4">{item.description}</p>
                    )}
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <div className="flex items-center">
                          <DollarSign className="h-4 w-4 mr-1" />
                          <span className="font-semibold text-gray-900">
                            ${item.value.toFixed(2)}
                          </span>
                        </div>
                        <div className="flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          <span>{item.ticket * 5} min</span>
                        </div>
                      </div>
                      
                      <button
                        onClick={(e) => handleAddToCart(item, e)}
                        disabled={isAdding || cartLoading}
                        className={`
                          flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium 
                          transition-all duration-200 ease-in-out
                          ${isAdding 
                            ? 'bg-gray-400 text-white cursor-not-allowed' 
                            : 'bg-primary-600 text-white hover:bg-primary-700 hover:scale-105 active:scale-95'
                          }
                        `}
                      >
                        {isAdding ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Adding...</span>
                          </>
                        ) : (
                          <>
                            <ShoppingCart className="h-4 w-4" />
                            <span>Add</span>
                          </>
                        )}
                      </button>
                    </div>
                    
                    {/* Click hint */}
                    <div className="mt-3 text-xs text-gray-400 text-center">
                      Click anywhere to add to cart
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
});

MenuList.displayName = 'MenuList';

export default MenuList;
