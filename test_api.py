import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json
from app.main import app

client = TestClient(app)

# Test data
TEST_ORDER = {
    "customer_name": "Test User",
    "items": [
        {"sku": "FUR001", "qty": 2},
        {"sku": "FUR002", "qty": 1}
    ]
}

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_inventory():
    """Test listing inventory items"""
    response = client.get("/inventory/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    if len(response.json()) > 0:
        assert "sku" in response.json()[0]
        assert "name" in response.json()[0]
        assert "stock" in response.json()[0]

def test_get_inventory_item():
    """Test getting a single inventory item"""
    # First get a valid SKU from the inventory
    response = client.get("/inventory/")
    if len(response.json()) > 0:
        sku = response.json()[0]["sku"]
        response = client.get(f"/inventory/{sku}")
        assert response.status_code == 200
        assert response.json()["sku"] == sku

def test_update_inventory():
    """Test updating inventory stock"""
    # Get an item to update
    response = client.get("/inventory/")
    if len(response.json()) > 0:
        sku = response.json()[0]["sku"]
        current_stock = response.json()[0]["stock"]
        
        # Update the stock
        new_stock = current_stock + 1
        update_data = {"stock": new_stock}
        response = client.patch(f"/inventory/{sku}", json=update_data)
        
        assert response.status_code == 200
        assert response.json()["stock"] == new_stock

def test_place_order():
    """Test placing a new order"""
    response = client.post("/orders/", json=TEST_ORDER)
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data
    assert data["status"] == "confirmed"
    return data["order_id"]  # Return order_id for other tests

def test_get_order():
    """Test retrieving an order"""
    # First place an order to get a valid order_id
    order_id = test_place_order()
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert data["customer_name"] == TEST_ORDER["customer_name"]

def test_place_order_insufficient_stock():
    """Test order placement with insufficient stock"""
    test_order = {
        "customer_name": "Test User",
        "items": [{"sku": "FUR001", "qty": 999999}]  # Unrealistically large quantity
    }
    response = client.post("/orders/", json=test_order)
    assert response.status_code == 200  # Should return 200 with partial fulfillment
    assert response.json()["partial_fulfilment"] is True

def test_place_order_invalid_sku():
    """Test order placement with invalid SKU"""
    test_order = {
        "customer_name": "Test User",
        "items": [{"sku": "INVALID_SKU", "qty": 1}]
    }
    response = client.post("/orders/", json=test_order)
    assert response.status_code == 400  # Bad Request

def test_get_nonexistent_order():
    """Test retrieving an order that doesn't exist"""
    response = client.get("/orders/999999")
    assert response.status_code == 404

def test_delete_order():
    """Test deleting an order"""
    # First place an order to delete
    order_id = test_place_order()
    
    # Delete the order
    response = client.delete(f"/orders/{order_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 404

def test_delete_nonexistent_order():
    """Test deleting an order that doesn't exist"""
    response = client.delete("/orders/999999")
    assert response.status_code == 404

def test_delete_orders_by_date_range():
    """Test deleting orders by date range"""
    # First create some test orders
    test_order1 = {
        "customer_name": "Test User 1",
        "items": [{"sku": "FUR001", "qty": 1}]
    }
    test_order2 = {
        "customer_name": "Test User 2",
        "items": [{"sku": "FUR002", "qty": 1}]
    }
    
    # Place orders
    client.post("/orders/", json=test_order1)
    client.post("/orders/", json=test_order2)
    
    # Delete orders from the last hour
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=1)
    
    # Format dates as ISO strings
    start_iso = start_date.isoformat()
    end_iso = end_date.isoformat()
    
    # Delete orders in date range
    response = client.delete(f"/orders/?start_date={start_iso}&end_date={end_iso}")
    assert response.status_code == 200
    assert response.json()["deleted_count"] >= 0

def test_delete_orders_by_status():
    """Test deleting orders by status"""
    # First create a test order
    test_order = {
        "customer_name": "Test User Status",
        "items": [{"sku": "FUR001", "qty": 1}]
    }
    client.post("/orders/", json=test_order)
    
    # Delete orders with status 'confirmed'
    response = client.delete("/orders/?status=confirmed")
    assert response.status_code == 200
    assert response.json()["deleted_count"] >= 0

def test_invalid_date_range():
    """Test with invalid date range"""
    response = client.delete("/orders/?start_date=invalid-date")
    assert response.status_code == 422  # Validation error