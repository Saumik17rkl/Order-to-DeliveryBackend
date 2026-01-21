from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from pymongo import ReturnDocument

from app.mongo import get_mongo_db
from app import schemas

router = APIRouter(prefix="/orders", tags=["orders"])

LOW_STOCK_THRESHOLD = 10


def get_db():
    return get_mongo_db()


def err(detail: dict, code: int):
    raise HTTPException(status_code=code, detail=detail)


# ==========================
# ORDER ID GENERATOR (FIXED)
# ==========================
def get_next_order_id(db, session):
    result = db.counters.find_one_and_update(
        {"_id": "order_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
        session=session
    )
    return result["seq"]


# ==========================
# PLACE ORDER
# ==========================
@router.post("/", response_model=schemas.OrderResponse)
def place_order(
    payload: schemas.OrderCreate,
    request: Request,
    db=Depends(get_db),
):
    trace = getattr(request.state, "trace_id", None)
    log = logger.bind(trace_id=trace)

    log.info(f"order request from {payload.customer_name}")

    # Prevent duplicate SKUs
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

    try:
        with db.client.start_session() as session:
            with session.start_transaction():

                order_id = get_next_order_id(db, session)

                fulfilment_items = []
                partial_fulfilment = False

                for item in payload.items:
                    inventory_item = db.inventory.find_one(
                        {"sku": item.sku},
                        session=session
                    )

                    if not inventory_item:
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

                    updated_inventory = None
                    if available_qty > 0:
                        updated_inventory = db.inventory.find_one_and_update(
                            {"sku": item.sku, "stock": {"$gte": available_qty}},
                            {"$inc": {"stock": -available_qty}},
                            return_document=ReturnDocument.AFTER,
                            session=session
                        )

                    if available_qty < item.qty:
                        partial_fulfilment = True

                    remaining_stock = (
                        updated_inventory["stock"]
                        if updated_inventory
                        else inventory_item["stock"]
                    )

                    fulfilment_items.append({
                        "sku": item.sku,
                        "requested_qty": item.qty,
                        "fulfilled_qty": available_qty,
                        "remaining_stock": remaining_stock,
                        "few_left": 0 < remaining_stock < LOW_STOCK_THRESHOLD
                    })

                order = {
                    "order_id": order_id,
                    "customer_name": payload.customer_name,
                    "status": "CONFIRMED",
                    "items": [{"sku": i.sku, "quantity": i.qty} for i in payload.items],
                    "total_items": sum(i.qty for i in payload.items),
                    "fulfilment_status": (
                        "FULLY_FULFILLED" if not partial_fulfilment else "PARTIALLY_FULFILLED"
                    ),
                    "created_at": datetime.utcnow(),
                }

                db.orders.insert_one(order, session=session)

                log.success(f"Order {order_id} placed successfully")

                return {
                    "success": True,
                    "order_id": order_id,
                    "status": "confirmed",
                    "fulfilment_status": (
                        "fully fulfilled" if not partial_fulfilment else "partially fulfilled"
                    ),
                    "partial_fulfilment": partial_fulfilment,
                    "items": fulfilment_items,
                    "message": "Order placed successfully",
                }


    except Exception as e:
        log.exception("Order processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "code": "order_processing_error",
                "message": str(e),
            },
        )


# ==========================
# GET ORDER
# ==========================
@router.get("/{order_id}", response_model=schemas.OrderDetail)
def get_order(order_id: int, request: Request, db=Depends(get_db)):
    trace = getattr(request.state, "trace_id", None)
    log = logger.bind(trace_id=trace)

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

    return {
        "id": order["order_id"],
        "customer_name": order["customer_name"],
        "status": order["status"],
        "total_items": order["total_items"],
        "items": order["items"],
    }
