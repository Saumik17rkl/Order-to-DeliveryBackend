from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from app.database import SessionLocal
from app import models, schemas

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def error(detail: dict, status_code: int):
    raise HTTPException(status_code=status_code, detail=detail)


# ==========================
#  PLACE ORDER
# ==========================

@router.post("/", response_model=schemas.OrderResponse)
def place_order(payload: schemas.OrderRequest, request: Request, db: Session = Depends(get_db)):

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

    try:
        with db.begin():

            # Validate + lock inventory
            inventory_items = {}
            for item in payload.items:
                inv = (
                    db.query(models.Inventory)
                    .filter(models.Inventory.sku == item.sku)
                    .with_for_update()
                    .first()
                )

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

                if inv.stock < item.qty:
                    log.warning(
                        f"Out of stock — SKU={item.sku} requested={item.qty} available={inv.stock}"
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

                inventory_items[item.sku] = inv

            # Deduct stock
            for item in payload.items:
                inventory_items[item.sku].stock -= item.qty
                db.add(inventory_items[item.sku])

            # Create order
            order = models.Orders(
                customer_name=payload.customer_name,
                status="CONFIRMED",
                total_items=sum(i.qty for i in payload.items),
            )
            db.add(order)
            db.flush()

            # Add order items
            for item in payload.items:
                order_item = models.OrderItems(
                    order_id=order.id, sku=item.sku, quantity=item.qty
                )
                db.add(order_item)

            log.success(f"Order CONFIRMED — order_id={order.id}")

            return {
                "order_id": order.id,
                "status": "CONFIRMED",
                "message": "Order validated and stock reserved.",
            }

    except HTTPException:
        raise

    except SQLAlchemyError:
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
def get_order(order_id: int, request: Request, db: Session = Depends(get_db)):

    log = logger.bind(trace_id=getattr(request.state, "trace_id", None))

    order = (
        db.query(models.Orders)
        .filter(models.Orders.id == order_id)
        .first()
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

    items = (
        db.query(models.OrderItems)
        .filter(models.OrderItems.order_id == order.id)
        .all()
    )

    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "status": order.status,
        "total_items": order.total_items,
        "items": [{"sku": i.sku, "quantity": i.quantity} for i in items],
    }
