from fastapi import APIRouter, Depends, HTTPException, status, Request
from loguru import logger
from pymongo import ReturnDocument

from app.mongo import get_mongo_db
from app import schemas

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_db():
    return get_mongo_db()


def get_next_order_id(db) -> int:
    doc = db["counters"].find_one_and_update(
        {"_id": "orders"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc["seq"])


def error(detail: dict, status_code: int):
    raise HTTPException(status_code=status_code, detail=detail)


# ==========================
#  PLACE ORDER
# ==========================

@router.post("/", response_model=schemas.OrderResponse)
def place_order(payload: schemas.OrderRequest, request: Request, db=Depends(get_db)):

    log = logger.bind(trace_id=getattr(request.state, "trace_id", None))

    # Normalize SKUs + detect duplicates
    seen = set()
    for item in payload.items:
        item.sku = item.sku.upper().strip()

        if item.sku in seen:
            log.warning(f"Duplicate SKU found in order → {item.sku}")
            error(
                {
                    "success": False,
                    "code": "DUPLICATE_SKU",
                    "message": "Duplicate SKU in order",
                    "sku": item.sku,
                },
                status.HTTP_400_BAD_REQUEST,
            )
        seen.add(item.sku)

    deducted: list[tuple[str, int]] = []

    try:
        inventory = db["inventory"]

        for item in payload.items:
            inv = inventory.find_one({"sku": item.sku}, {"_id": 0, "sku": 1, "stock": 1})
            if not inv:
                log.warning(f"Invalid SKU in order → {item.sku}")
                error(
                    {
                        "success": False,
                        "code": "INVALID_SKU",
                        "message": "SKU not found",
                        "sku": item.sku,
                    },
                    status.HTTP_400_BAD_REQUEST,
                )

            update = inventory.update_one(
                {"sku": item.sku, "stock": {"$gte": item.qty}},
                {"$inc": {"stock": -item.qty}},
            )

            if update.modified_count == 0:
                log.warning(
                    f"Out of stock — SKU={item.sku} requested={item.qty}"
                )
                error(
                    {
                        "success": False,
                        "code": "OUT_OF_STOCK",
                        "message": "Requested quantity not available",
                        "sku": item.sku,
                    },
                    status.HTTP_400_BAD_REQUEST,
                )

            deducted.append((item.sku, item.qty))

        order_id = get_next_order_id(db)

        db["orders"].insert_one(
            {
                "order_id": order_id,
                "customer_name": payload.customer_name,
                "status": "CONFIRMED",
                "total_items": sum(i.qty for i in payload.items),
                "items": [{"sku": i.sku, "quantity": i.qty} for i in payload.items],
            }
        )

        log.success(f"Order CONFIRMED — order_id={order_id}")

        return {
            "order_id": order_id,
            "status": "CONFIRMED",
            "message": "Order validated and stock reserved.",
        }

    except HTTPException:
        for sku, qty in deducted:
            db["inventory"].update_one({"sku": sku}, {"$inc": {"stock": qty}})
        raise

    except Exception:
        for sku, qty in deducted:
            db["inventory"].update_one({"sku": sku}, {"$inc": {"stock": qty}})

        log.exception("Database error during order placement")
        error(
            {
                "success": False,
                "code": "DB_ERROR",
                "message": "Database failure",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ==========================
#  GET ORDER
# ==========================

@router.get("/{order_id}", response_model=schemas.OrderDetail)
def get_order(order_id: int, request: Request, db=Depends(get_db)):

    log = logger.bind(trace_id=getattr(request.state, "trace_id", None))

    order = db["orders"].find_one(
        {"order_id": order_id},
        {"_id": 0, "order_id": 1, "customer_name": 1, "status": 1, "total_items": 1, "items": 1},
    )

    if not order:
        log.warning(f"Order not found — id={order_id}")
        error(
            {
                "success": False,
                "code": "ORDER_NOT_FOUND",
                "message": "Order does not exist",
            },
            status.HTTP_404_NOT_FOUND,
        )

    return {
        "id": order["order_id"],
        "customer_name": order["customer_name"],
        "status": order["status"],
        "total_items": order["total_items"],
        "items": order.get("items", []),
    }
