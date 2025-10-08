"""
Tests for cart endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestCart:
    """Test cart endpoints"""
    
    def test_get_cart_items_empty(self, client: TestClient, auth_headers):
        """Test getting cart items when cart is empty"""
        response = client.get("/api/v1/cart/items", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 0
        assert data["total_value"] == 0.0
        assert data["total_tickets"] == 0
        assert len(data["items"]) == 0
    
    def test_add_to_cart(self, client: TestClient, auth_headers, test_food_items):
        """Test adding item to cart"""
        item_id = test_food_items[0].id
        cart_data = {
            "food_item_id": item_id,
            "quantity": 2
        }
        
        response = client.post(
            "/api/v1/cart/items",
            json=cart_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["food_item_id"] == item_id
        assert data["quantity"] == 2
        assert data["food_item"]["name"] == "Test Wings"
    
    def test_add_to_cart_invalid_item(self, client: TestClient, auth_headers):
        """Test adding non-existent item to cart"""
        cart_data = {
            "food_item_id": 999,
            "quantity": 1
        }
        
        response = client.post(
            "/api/v1/cart/items",
            json=cart_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_cart_items_with_items(self, client: TestClient, auth_headers, test_food_items):
        """Test getting cart items when cart has items"""
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
        
        # Get cart items
        response = client.get("/api/v1/cart/items", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 3  # 2 + 1
        assert data["total_value"] == 44.97  # (12.99 * 2) + (18.99 * 1)
        assert data["total_tickets"] == 4  # (1 * 2) + (2 * 1)
        assert len(data["items"]) == 2
    
    def test_add_same_item_multiple_times(self, client: TestClient, auth_headers, test_food_items):
        """Test adding the same item multiple times (should increase quantity)"""
        item_id = test_food_items[0].id
        
        # Add item first time
        client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=auth_headers
        )
        
        # Add same item second time
        response = client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 2},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 3  # 1 + 2
        
        # Verify total in cart
        cart_response = client.get("/api/v1/cart/items", headers=auth_headers)
        cart_data = cart_response.json()
        assert cart_data["total_items"] == 3
    
    def test_update_cart_item_quantity(self, client: TestClient, auth_headers, test_food_items):
        """Test updating cart item quantity"""
        item_id = test_food_items[0].id
        
        # Add item to cart
        add_response = client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=auth_headers
        )
        cart_item_id = add_response.json()["id"]
        
        # Update quantity
        update_data = {"quantity": 5}
        response = client.put(
            f"/api/v1/cart/items/{cart_item_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 5
    
    def test_update_cart_item_not_found(self, client: TestClient, auth_headers):
        """Test updating non-existent cart item"""
        update_data = {"quantity": 5}
        response = client.put(
            "/api/v1/cart/items/999",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_remove_cart_item(self, client: TestClient, auth_headers, test_food_items):
        """Test removing item from cart"""
        item_id = test_food_items[0].id
        
        # Add item to cart
        add_response = client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=auth_headers
        )
        cart_item_id = add_response.json()["id"]
        
        # Remove item
        response = client.delete(
            f"/api/v1/cart/items/{cart_item_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "removed from cart" in data["message"]
        
        # Verify item is removed
        cart_response = client.get("/api/v1/cart/items", headers=auth_headers)
        cart_data = cart_response.json()
        assert cart_data["total_items"] == 0
    
    def test_remove_cart_item_not_found(self, client: TestClient, auth_headers):
        """Test removing non-existent cart item"""
        response = client.delete(
            "/api/v1/cart/items/999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_clear_cart(self, client: TestClient, auth_headers, test_food_items):
        """Test clearing entire cart"""
        # Add multiple items to cart
        for item in test_food_items:
            client.post(
                "/api/v1/cart/items",
                json={"food_item_id": item.id, "quantity": 1},
                headers=auth_headers
            )
        
        # Clear cart
        response = client.delete("/api/v1/cart/clear", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "cleared successfully" in data["message"]
        
        # Verify cart is empty
        cart_response = client.get("/api/v1/cart/items", headers=auth_headers)
        cart_data = cart_response.json()
        assert cart_data["total_items"] == 0
    
    def test_increase_item_quantity(self, client: TestClient, auth_headers, test_food_items):
        """Test increasing cart item quantity"""
        item_id = test_food_items[0].id
        
        # Add item to cart
        add_response = client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=auth_headers
        )
        cart_item_id = add_response.json()["id"]
        
        # Increase quantity
        response = client.post(
            f"/api/v1/cart/items/{cart_item_id}/increase",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "increased" in data["message"]
        assert data["item"]["quantity"] == 2
    
    def test_decrease_item_quantity(self, client: TestClient, auth_headers, test_food_items):
        """Test decreasing cart item quantity"""
        item_id = test_food_items[0].id
        
        # Add item to cart with quantity 2
        add_response = client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 2},
            headers=auth_headers
        )
        cart_item_id = add_response.json()["id"]
        
        # Decrease quantity
        response = client.post(
            f"/api/v1/cart/items/{cart_item_id}/decrease",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "decreased" in data["message"]
        assert data["item"]["quantity"] == 1
    
    def test_decrease_item_quantity_to_zero(self, client: TestClient, auth_headers, test_food_items):
        """Test decreasing cart item quantity to zero (should remove item)"""
        item_id = test_food_items[0].id
        
        # Add item to cart with quantity 1
        add_response = client.post(
            "/api/v1/cart/items",
            json={"food_item_id": item_id, "quantity": 1},
            headers=auth_headers
        )
        cart_item_id = add_response.json()["id"]
        
        # Decrease quantity to zero
        response = client.post(
            f"/api/v1/cart/items/{cart_item_id}/decrease",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "removed from cart" in data["message"]
    
    def test_cart_requires_authentication(self, client: TestClient):
        """Test that cart endpoints require authentication"""
        # Get cart items without auth
        response = client.get("/api/v1/cart/items")
        assert response.status_code == 403
        
        # Add to cart without auth
        response = client.post("/api/v1/cart/items", json={"food_item_id": 1, "quantity": 1})
        assert response.status_code == 403
