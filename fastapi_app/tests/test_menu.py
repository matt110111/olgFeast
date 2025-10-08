"""
Tests for menu endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestMenu:
    """Test menu endpoints"""
    
    def test_get_food_items(self, client: TestClient, test_food_items):
        """Test getting all food items"""
        response = client.get("/api/v1/menu/items")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "Test Wings"
        assert data[1]["name"] == "Test Burger"
        assert data[2]["name"] == "Test Cake"
    
    def test_get_food_items_with_filter(self, client: TestClient, test_food_items):
        """Test getting food items with group filter"""
        response = client.get("/api/v1/menu/items?food_group=Appetizers")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Wings"
        assert data[0]["food_group"] == "Appetizers"
    
    def test_get_food_items_pagination(self, client: TestClient, test_food_items):
        """Test getting food items with pagination"""
        response = client.get("/api/v1/menu/items?skip=1&limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    def test_get_food_groups(self, client: TestClient, test_food_items):
        """Test getting food groups"""
        response = client.get("/api/v1/menu/items/groups")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        groups = [group["group"] for group in data]
        assert "Appetizers" in groups
        assert "Main Course" in groups
        assert "Desserts" in groups
    
    def test_get_food_item_by_id(self, client: TestClient, test_food_items):
        """Test getting a specific food item"""
        item_id = test_food_items[0].id
        response = client.get(f"/api/v1/menu/items/{item_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["name"] == "Test Wings"
    
    def test_get_food_item_not_found(self, client: TestClient):
        """Test getting non-existent food item"""
        response = client.get("/api/v1/menu/items/999")
        
        assert response.status_code == 404
    
    def test_create_food_item(self, client: TestClient, staff_auth_headers):
        """Test creating a food item (staff only)"""
        item_data = {
            "food_group": "Beverages",
            "name": "Test Coffee",
            "value": 4.99,
            "ticket": 1,
            "description": "Fresh brewed coffee"
        }
        
        response = client.post(
            "/api/v1/menu/items",
            json=item_data,
            headers=staff_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Coffee"
        assert data["food_group"] == "Beverages"
        assert data["value"] == 4.99
    
    def test_create_food_item_unauthorized(self, client: TestClient, auth_headers):
        """Test creating food item without staff privileges"""
        item_data = {
            "food_group": "Beverages",
            "name": "Test Coffee",
            "value": 4.99,
            "ticket": 1
        }
        
        response = client.post(
            "/api/v1/menu/items",
            json=item_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_create_food_item_no_auth(self, client: TestClient):
        """Test creating food item without authentication"""
        item_data = {
            "food_group": "Beverages",
            "name": "Test Coffee",
            "value": 4.99,
            "ticket": 1
        }
        
        response = client.post("/api/v1/menu/items", json=item_data)
        
        assert response.status_code == 403
    
    def test_update_food_item(self, client: TestClient, test_food_items, staff_auth_headers):
        """Test updating a food item (staff only)"""
        item_id = test_food_items[0].id
        update_data = {
            "name": "Updated Wings",
            "value": 15.99
        }
        
        response = client.put(
            f"/api/v1/menu/items/{item_id}",
            json=update_data,
            headers=staff_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Wings"
        assert data["value"] == 15.99
    
    def test_update_food_item_not_found(self, client: TestClient, staff_auth_headers):
        """Test updating non-existent food item"""
        update_data = {
            "name": "Updated Item"
        }
        
        response = client.put(
            "/api/v1/menu/items/999",
            json=update_data,
            headers=staff_auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_food_item(self, client: TestClient, test_food_items, staff_auth_headers):
        """Test deleting a food item (staff only)"""
        item_id = test_food_items[0].id
        
        response = client.delete(
            f"/api/v1/menu/items/{item_id}",
            headers=staff_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        # Verify item is deleted
        get_response = client.get(f"/api/v1/menu/items/{item_id}")
        assert get_response.status_code == 404
    
    def test_delete_food_item_not_found(self, client: TestClient, staff_auth_headers):
        """Test deleting non-existent food item"""
        response = client.delete(
            "/api/v1/menu/items/999",
            headers=staff_auth_headers
        )
        
        assert response.status_code == 404
