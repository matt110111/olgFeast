"""
Tests for order endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.models.order import OrderStatus


class TestOrders:
    """Test order endpoints"""
    
    def test_create_order_empty_cart(self, client: TestClient, auth_headers):
        """Test creating order with empty cart"""
        order_data = {"customer_name": "Test Customer"}
        
        response = client.post(
            "/api/v1/orders/checkout",
            json=order_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Cart is empty" in response.json()["detail"]
    
    def test_create_order(self, client: TestClient, auth_headers, test_food_items):
        """Test creating order from cart"""
        # Add items to cart
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
        
        # Create order
        order_data = {"customer_name": "Test Customer"}
        response = client.post(
            "/api/v1/orders/checkout",
            json=order_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["customer_name"] == "Test Customer"
        assert data["status"] == "pending"
        assert "ref_code" in data
        assert len(data["order_items"]) == 3  # 2 + 1 items
        
        # Verify cart is cleared
        cart_response = client.get("/api/v1/cart/items", headers=auth_headers)
        cart_data = cart_response.json()
        assert cart_data["total_items"] == 0
    
    def test_get_my_orders(self, client: TestClient, auth_headers, test_food_items):
        """Test getting user's orders"""
        # Create an order first
        item_id = test_food_items[0].id
        client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=auth_headers
        )
        
        client.post(
            "/api/v1/orders/checkout",
            json={"customer_name": "Test Customer"},
            headers=auth_headers
        )
        
        # Get orders
        response = client.get("/api/v1/orders/my-orders", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["customer_name"] == "Test Customer"
        assert data[0]["status"] == "pending"
    
    def test_get_my_order_by_id(self, client: TestClient, auth_headers, test_food_items):
        """Test getting specific user order"""
        # Create an order first
        item_id = test_food_items[0].id
        client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=auth_headers
        )
        
        order_response = client.post(
            "/api/v1/orders/checkout",
            json={"customer_name": "Test Customer"},
            headers=auth_headers
        )
        order_id = order_response.json()["id"]
        
        # Get specific order
        response = client.get(f"/api/v1/orders/my-orders/{order_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["customer_name"] == "Test Customer"
        assert len(data["order_items"]) == 1
    
    def test_get_my_order_not_found(self, client: TestClient, auth_headers):
        """Test getting non-existent user order"""
        response = client.get("/api/v1/orders/my-orders/999", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_get_all_orders_staff(self, client: TestClient, staff_auth_headers, test_food_items):
        """Test getting all orders (staff only)"""
        # Create an order first
        item_id = test_food_items[0].id
        client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=staff_auth_headers
        )
        
        client.post(
            "/api/v1/orders/checkout",
            json={"customer_name": "Test Customer"},
            headers=staff_auth_headers
        )
        
        # Get all orders
        response = client.get("/api/v1/orders/", headers=staff_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["customer_name"] == "Test Customer"
    
    def test_get_all_orders_non_staff(self, client: TestClient, auth_headers):
        """Test getting all orders without staff privileges"""
        response = client.get("/api/v1/orders/", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_update_order_status(self, client: TestClient, staff_auth_headers, test_food_items):
        """Test updating order status (staff only)"""
        # Create an order first
        item_id = test_food_items[0].id
        client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=staff_auth_headers
        )
        
        order_response = client.post(
            "/api/v1/orders/checkout",
            json={"customer_name": "Test Customer"},
            headers=staff_auth_headers
        )
        order_id = order_response.json()["id"]
        
        # Update status
        status_data = {"status": "preparing"}
        response = client.put(
            f"/api/v1/orders/{order_id}/status",
            json=status_data,
            headers=staff_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "preparing"
        assert data["date_preparing"] is not None
    
    def test_update_order_status_invalid(self, client: TestClient, staff_auth_headers, test_food_items):
        """Test updating order status with invalid status"""
        # Create an order first
        item_id = test_food_items[0].id
        client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=staff_auth_headers
        )
        
        order_response = client.post(
            "/api/v1/orders/checkout",
            json={"customer_name": "Test Customer"},
            headers=staff_auth_headers
        )
        order_id = order_response.json()["id"]
        
        # Update with invalid status
        status_data = {"status": "invalid_status"}
        response = client.put(
            f"/api/v1/orders/{order_id}/status",
            json=status_data,
            headers=staff_auth_headers
        )
        
        assert response.status_code == 400
    
    def test_update_order_status_not_found(self, client: TestClient, staff_auth_headers):
        """Test updating status of non-existent order"""
        status_data = {"status": "preparing"}
        response = client.put(
            "/api/v1/orders/999/status",
            json=status_data,
            headers=staff_auth_headers
        )
        
        assert response.status_code == 404
    
    def test_update_order_status_non_staff(self, client: TestClient, auth_headers, test_food_items):
        """Test updating order status without staff privileges"""
        # Create an order first
        item_id = test_food_items[0].id
        client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=auth_headers
        )
        
        order_response = client.post(
            "/api/v1/orders/checkout",
            json={"customer_name": "Test Customer"},
            headers=auth_headers
        )
        order_id = order_response.json()["id"]
        
        # Try to update status without staff privileges
        status_data = {"status": "preparing"}
        response = client.put(
            f"/api/v1/orders/{order_id}/status",
            json=status_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_get_order_analytics_staff(self, client: TestClient, staff_auth_headers, test_food_items):
        """Test getting order analytics (staff only)"""
        # Create an order first
        item_id = test_food_items[0].id
        client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=staff_auth_headers
        )
        
        client.post(
            "/api/v1/orders/checkout",
            json={"customer_name": "Test Customer"},
            headers=staff_auth_headers
        )
        
        # Get analytics
        response = client.get("/api/v1/orders/analytics/dashboard", headers=staff_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "orders_today" in data
        assert "status_counts" in data
        assert "total_revenue" in data
    
    def test_get_order_analytics_non_staff(self, client: TestClient, auth_headers):
        """Test getting order analytics without staff privileges"""
        response = client.get("/api/v1/orders/analytics/dashboard", headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_orders_require_authentication(self, client: TestClient):
        """Test that order endpoints require authentication"""
        # Create order without auth
        response = client.post("/api/v1/orders/checkout", json={"customer_name": "Test"})
        assert response.status_code == 403
        
        # Get orders without auth
        response = client.get("/api/v1/orders/my-orders")
        assert response.status_code == 403
