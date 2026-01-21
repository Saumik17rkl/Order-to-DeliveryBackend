from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from typing import List
from pymongo import ReturnDocument

from app.mongo import get_mongo_db
from app import schemas

router = APIRouter(prefix="/orders", tags=["orders"])


def get_db():
    return get_mongo_db()


def err(detail: dict, code: int):
    raise HTTPException(status_code=code, detail=detail)


def get_next_order_id(db):
    # First, check if the counters collection exists and has the order_id counter
    counter = db.counters.find_one({"_id": "order_id"})
    
    if counter:
        # If counter exists, increment and return
        result = db.counters.find_one_and_update(
            {"_id": "order_id"},
            {"$inc": {"seq": 1}},
            return_document=ReturnDocument.AFTER
        )
        return result["seq"]
    else:
        # If no counter exists, check the orders collection for the highest order_id
        last_order = db.orders.find_one(
            {},
            sort=[("order_id", -1)]  # Sort by order_id in descending order
        )
        
        if last_order:
            # If orders exist, start from the highest order_id + 1
            new_id = last_order["order_id"] 
        else:
            # If no orders exist, start from 1
            new_id = 1
        
        # Create the counter for future use
        db.counters.insert_one({
            "_id": "order_id",
            "seq": new_id
        })
        
        return new_id

# ==========================
#  PLACE ORDER
# ==========================

@router.post("/", response_model=schemas.OrderResponse)
def place_order(
    payload: schemas.OrderCreate,
    request: Request,
    db = Depends(get_db),
    ):
    trace = getattr(request.state, "trace_id", None)
    log = logger.bind(trace_id=trace)
    
    log.info(f"order request from {payload.customer_name}")
    
    # Verify MongoDB collections exist and are accessible
    try:
        collections = db.list_collection_names()
        log.info(f"Available collections: {collections}")
        if 'inventory' not in collections or 'orders' not in collections or 'counters' not in collections:
            log.error("Required collections (inventory, orders, counters) not found in database")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "code": "database_error",
                    "message": "Required database collections not found"
                }
            )
    except Exception as e:
        log.error(f"Error accessing database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "code": "database_connection_error",
                "message": f"Error accessing database: {str(e)}"
            }
        )

    try:
        # prevent duplicate SKUs
        seen = set()
        for item in payload.items:
            item.sku = item.sku.upper().strip()
            if item.sku in seen:
                err(
                    {
                        "success": False,
                        "code": "duplicate_sku",
                        "message": "duplicate sku in order",
                        "sku": item.sku,
                    },
                    status.HTTP_400_BAD_REQUEST,
                )
            seen.add(item.sku)

        # Start a session for atomic operations
        with db.client.start_session() as session:
            with session.start_transaction():
                # Get next order ID
                order_id = get_next_order_id(db)
                
                fulfilment_items = []
                partial_fulfilment = False
                fulfilled_total = 0

                for item in payload.items:
                    # First check if SKU exists and get current stock
                    inventory_item = db.inventory.find_one(
                        {"sku": item.sku},
                        session=session
                    )
                    
                    if not inventory_item:
                        session.abort_transaction()
                        err(
                            {
                                "success": False,
                                "code": "invalid_sku",
                                "message": f"SKU {item.sku} not found",
                                "sku": item.sku,
                            },
                            status.HTTP_400_BAD_REQUEST,
                        )
                    
                    available_qty = min(item.qty, inventory_item["stock"])
                    
                    if available_qty > 0:
                        # Update inventory if we can fulfill at least 1 item
                        result = db.inventory.find_one_and_update(
                            {"sku": item.sku, "stock": {"$gte": 1}},
                            {"$inc": {"stock": -available_qty}},
                            return_document=ReturnDocument.AFTER,
                            session=session
                        )
                        
                        if not result:
                            # This should theoretically not happen since we just checked stock
                            available_qty = 0
                    else:
                        available_qty = 0
                    
                    # Track if this item was partially fulfilled
                    if available_qty < item.qty:
                        partial_fulfilment = True
                    
                    # Add to fulfilled items with actual fulfilled quantity
                    remaining_stock = inventory_item["stock"] - available_qty if available_qty > 0 else 0
                    fulfilled_items = {
                        "sku": item.sku,
                        "requested_qty": item.qty,
                        "fulfilled_qty": available_qty,
                        "remaining_stock": remaining_stock,
                        "few_left": 0 < remaining_stock < 10
                    }
                    
                    if available_qty > 0:
                        fulfilled_total += available_qty
                        fulfilment_items.append(fulfilled_items)
                    
                    # If we couldn't fulfill any items, add to the response but with 0 fulfilled
                    if available_qty == 0:
                        fulfilment_items.append(fulfilled_items)

                # Create order
                order = {
                    "order_id": order_id,
                    "customer_name": payload.customer_name,
                    "status": "confirmed",
                    "items": [{"sku": item.sku, "quantity": item.qty} for item in payload.items],
                    "total_items": sum(item.qty for item in payload.items),
                    "fulfilment_status": "fully fulfilled" if not partial_fulfilment else "partially fulfilled",
                    "created_at": datetime.utcnow()
                }
                
                db.orders.insert_one(order, session=session)
                
                log.success(f"Order {order_id} placed successfully for {payload.customer_name}")
                
                return {
                    "success": True,
                    "order_id": order_id,
                    "status": "confirmed",
                    "fulfilment_status": "fully fulfilled" if not partial_fulfilment else "partially fulfilled",
                    "partial_fulfilment": partial_fulfilment,
                    "items": fulfilment_items,
                    "message": "Order placed successfully"
                }

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log.error(f"Error placing order: {str(e)}\n{error_trace}")
        
        # Print the full exception to console for debugging
        print(f"\n=== DEBUG: Order Processing Error ===")
        print(f"Error: {str(e)}")
        print(f"Traceback:\n{error_trace}")
        print("Request Payload:", payload.dict())
        print("==============================\n")
        
        if 'session' in locals() and hasattr(session, 'in_transaction') and session.in_transaction:
            try:
                session.abort_transaction()
                log.info("Transaction aborted successfully")
            except Exception as abort_error:
                log.error(f"Error aborting transaction: {str(abort_error)}")
        
        # Return more detailed error information in development
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "code": "order_processing_error",
                "message": f"Error processing order: {str(e)}",
                "error_type": str(type(e).__name__),
                "details": str(e) if str(e) else "No additional details"
            }
        )


# GET ORDER

@router.get("/{order_id}", response_model=schemas.OrderDetail)
def get_order(order_id: int, request: Request, db = Depends(get_db)):
    trace = getattr(request.state, "trace_id", None)
    log = logger.bind(trace_id=trace)

    log.info(f"fetching order {order_id}")

    # Find the order and include the _id field for debugging
    order = db.orders.find_one({"order_id": order_id}, {"_id": 0})
    
    if not order:
        err(
            {
                "success": False,
                "code": "order_not_found",
                "message": "order not found",
                "order_id": order_id,
            },
            status.HTTP_404_NOT_FOUND,
        )

    # Convert status to uppercase to match the expected format
    order_status = order.get("status", "").upper()

    return {
        "id": order["order_id"],
        "customer_name": order["customer_name"],
        "status": order_status,
        "total_items": order["total_items"],
        "items": order["items"]
    }
