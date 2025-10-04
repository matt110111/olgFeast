import React, { useState, useEffect } from 'react';
import { FoodItem, FoodItemGroup } from '../../types';
import { apiService } from '../../services/api';
import { ShoppingCart, DollarSign, Clock } from 'lucide-react';

const MenuList: React.FC = () => {
  const [foodGroups, setFoodGroups] = useState<FoodItemGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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

  const handleAddToCart = async (foodItem: FoodItem) => {
    try {
      await apiService.addToCart({
        food_item_id: foodItem.id,
        quantity: 1,
      });
      // Could add a toast notification here
      console.log(`Added ${foodItem.name} to cart`);
    } catch (error) {
      console.error('Failed to add item to cart:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        <span className="sr-only">Loading...</span>
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
            {group.items.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
              >
                <div className="p-6">
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
                      onClick={() => handleAddToCart(item)}
                      className="flex items-center space-x-1 bg-primary-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
                    >
                      <ShoppingCart className="h-4 w-4" />
                      <span>Add</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default MenuList;
