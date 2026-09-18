"""
Performance tests for FastAPI endpoints
"""
import pytest
import time
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
import threading


class TestPerformance:
    """Performance tests for API endpoints"""
    
    def test_menu_items_performance(self, client: TestClient, test_food_items):
        """Test menu items endpoint performance"""
        start_time = time.time()
        
        response = client.get("/api/v1/menu/items")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
        
        print(f"Menu items endpoint response time: {response_time:.3f}s")
    
    def test_concurrent_menu_requests(self, client: TestClient, test_food_items):
        """Test concurrent requests to menu endpoint"""
        def make_request():
            response = client.get("/api/v1/menu/items")
            return response.status_code == 200
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        assert all(results), "Some requests failed"
        assert total_time < 5.0  # All 50 requests should complete within 5 seconds
        
        print(f"50 concurrent menu requests completed in: {total_time:.3f}s")
    
    def test_cart_operations_performance(self, client: TestClient, auth_headers, test_food_items):
        """Test cart operations performance"""
        item_id = test_food_items[0].id
        
        # Test add to cart
        start_time = time.time()
        response = client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=auth_headers
        )
        add_time = time.time() - start_time
        
        assert response.status_code == 200
        assert add_time < 0.5  # Add to cart should be fast
        
        cart_item_id = response.json()["id"]
        
        # Test get cart
        start_time = time.time()
        response = client.get("/api/v1/cart/items", headers=auth_headers)
        get_time = time.time() - start_time
        
        assert response.status_code == 200
        assert get_time < 0.5  # Get cart should be fast
        
        # Test update cart
        start_time = time.time()
        response = client.put(
            f"/api/v1/cart/items/{cart_item_id}",
            json={"quantity": 2},
            headers=auth_headers
        )
        update_time = time.time() - start_time
        
        assert response.status_code == 200
        assert update_time < 0.5  # Update cart should be fast
        
        print(f"Cart operations performance:")
        print(f"  Add to cart: {add_time:.3f}s")
        print(f"  Get cart: {get_time:.3f}s")
        print(f"  Update cart: {update_time:.3f}s")
    
    def test_order_creation_performance(self, client: TestClient, auth_headers, test_food_items):
        """Test order creation performance"""
        # Add items to cart first
        item1_id = test_food_items[0].id
        item2_id = test_food_items[1].id
        
        client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item1_id, "quantity": 2},
            headers=auth_headers
        )
        client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item2_id, "quantity": 1},
            headers=auth_headers
        )
        
        # Test order creation
        start_time = time.time()
        response = client.post(
            "/api/v1/orders/checkout",
            json={"customer_name": "Performance Test Customer"},
            headers=auth_headers
        )
        order_time = time.time() - start_time
        
        assert response.status_code == 200
        assert order_time < 2.0  # Order creation should complete within 2 seconds
        
        print(f"Order creation time: {order_time:.3f}s")
    
    def test_authentication_performance(self, client: TestClient, test_user):
        """Test authentication performance"""
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        # Test login
        start_time = time.time()
        response = client.post("/api/v1/auth/login", data=login_data)
        login_time = time.time() - start_time
        
        assert response.status_code == 200
        assert login_time < 1.0  # Login should be fast
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test authenticated request
        start_time = time.time()
        response = client.get("/api/v1/auth/me", headers=headers)
        auth_time = time.time() - start_time
        
        assert response.status_code == 200
        assert auth_time < 0.5  # Authenticated requests should be fast
        
        print(f"Authentication performance:")
        print(f"  Login: {login_time:.3f}s")
        print(f"  Authenticated request: {auth_time:.3f}s")
    
    def test_database_query_performance(self, client: TestClient, test_food_items):
        """Test database query performance with pagination"""
        # Test with different page sizes
        page_sizes = [10, 50, 100]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = client.get(f"/api/v1/menu/items?limit={page_size}")
            query_time = time.time() - start_time
            
            assert response.status_code == 200
            assert query_time < 1.0  # Database queries should be fast
            
            print(f"Database query with limit {page_size}: {query_time:.3f}s")
    
    def test_memory_usage(self, client: TestClient, test_food_items):
        """Test memory usage during heavy operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests
        for _ in range(100):
            response = client.get("/api/v1/menu/items")
            assert response.status_code == 200
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage:")
        print(f"  Initial: {initial_memory:.2f} MB")
        print(f"  Final: {final_memory:.2f} MB")
        print(f"  Increase: {memory_increase:.2f} MB")
        
        # Memory increase should be reasonable (less than 50MB for 100 requests)
        assert memory_increase < 50.0
