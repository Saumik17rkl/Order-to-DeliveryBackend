# test_api.py
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_inventory():
    """Test listing all inventory items"""
    response = client.get("/inventory/")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    for item in items:
        assert "sku" in item
        assert "name" in item
        assert "stock" in item
        assert "status" in item

def test_get_inventory_item():
    """Test getting a specific inventory item"""
    # First get a valid SKU from the inventory
    response = client.get("/inventory/")
    assert response.status_code == 200
    items = response.json()
    if items:
        sku = items[0]["sku"]
        response = client.get(f"/inventory/{sku}")
        assert response.status_code == 200
        item = response.json()
        assert item["sku"] == sku

def test_update_inventory():
    """Test updating inventory stock"""
    # Get an existing item to update
    response = client.get("/inventory/")
    assert response.status_code == 200
    items = response.json()
    if items:
        item = items[0]
        update_data = {"stock": item["stock"] + 1}
        response = client.patch(
            f"/inventory/{item['sku']}",
            json=update_data
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["stock"] == update_data["stock"]

def test_place_order():
    """Test placing a new order"""
    order_data = {
        "customer_name": "Test User",
        "items": [{"sku": "FUR001", "qty": 1}]
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 200
    order = response.json()
    assert "order_id" in order
    assert order["status"] == "confirmed"
    return order["order_id"]

def test_get_order():
    """Test retrieving an existing order"""
    # First create an order
    order_id = test_place_order()
    # Then try to retrieve it
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    order = response.json()
    assert order["id"] == order_id

def test_place_order_insufficient_stock():
    """Test order placement with insufficient stock"""
    order_data = {
        "customer_name": "Test User",
        "items": [{"sku": "FUR001", "qty": 1000}]  # Assuming we don't have this much stock
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 200  # Should still be 200 but with partial fulfillment
    order = response.json()
    assert order["partial_fulfilment"] is True

def test_place_order_invalid_sku():
    """Test order placement with invalid SKU"""
    order_data = {
        "customer_name": "Test User",
        "items": [{"sku": "INVALID_SKU", "qty": 1}]
    }
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 400  # Should be 400 for invalid SKU

def test_get_nonexistent_order():
    """Test retrieving a non-existent order"""
    response = client.get("/orders/999999")  # Assuming this ID doesn't exist
    assert response.status_code == 404