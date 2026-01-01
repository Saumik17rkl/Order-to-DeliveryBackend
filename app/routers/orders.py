from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from typing import List

from app.database import SessionLocal
from app import models, schemas

from app.mongo import get_mongo_db
from app import schemas

router = APIRouter(prefix="/orders", tags=["orders"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def err(detail: dict, code: int):
    raise HTTPException(status_code=code, detail=detail)


# ==========================
#  PLACE ORDER
# ==========================

@router.post("/", response_model=schemas.OrderResponse)
def place_order(
    payload: schemas.OrderCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    trace = getattr(request.state, "trace_id", None)
    log = logger.bind(trace_id=trace)

    log.info(f"order request from {payload.customer_name}")

    try:
        with db.begin():

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

            # create order record
            order = models.Orders(
                customer_name=payload.customer_name,
                status="pending",
            )
            db.add(order)
            db.flush()

            fulfilment_items: List[dict] = []
            partial_fulfilment = False
            fulfilled_total = 0

            for item in payload.items:

                inv = (
                    db.query(models.Inventory)
                    .filter(models.Inventory.sku == item.sku)
                    .with_for_update()
                    .first()
                )

                if not inv:
                    err(
                        {
                            "success": False,
                            "code": "invalid_sku",
                            "message": "sku not found",
                            "sku": item.sku,
                        },
                        status.HTTP_400_BAD_REQUEST,
                    )

                if inv.stock == 0:
                    err(
                        {
                            "success": False,
                            "code": "out_of_stock",
                            "message": "item is out of stock",
                            "sku": item.sku,
                        },
                        status.HTTP_400_BAD_REQUEST,
                    )

                fulfilled_qty = min(item.qty, inv.stock)

                if fulfilled_qty < item.qty:
                    partial_fulfilment = True

                inv.stock -= fulfilled_qty
                fulfilled_total += fulfilled_qty

                db.add(
                    models.OrderItems(
                        order_id=order.id,
                        sku=item.sku,
                        quantity=fulfilled_qty,
                    )
                )

                fulfilment_items.append(
                    {
                        "sku": item.sku,
                        "requested_qty": item.qty,
                        "fulfilled_qty": fulfilled_qty,
                        "remaining_stock": max(inv.stock, 0),
                        "few_left": (inv.stock > 0 and inv.stock < 10),
                    }
                )

            order.status = "confirmed"
            order.total_items = fulfilled_total
            db.add(order)

        fulfilment_status = (
            "partially fulfilled" if partial_fulfilment else "fully fulfilled"
        )

        log.success(f"order confirmed — id={order.id}")

        return {
            "success": True,
            "order_id": order.id,
            "status": "confirmed",
            "fulfilment_status": fulfilment_status,
            "partial_fulfilment": partial_fulfilment,
            "items": fulfilment_items,
            "message": "order validated and stock reserved",
        }

    except HTTPException:
        for sku, qty in deducted:
            db["inventory"].update_one({"sku": sku}, {"$inc": {"stock": qty}})
        raise

    except SQLAlchemyError:
        log.exception("database error during order placement")
        err(
            {
                "success": False,
                "code": "db_error",
                "message": "database failure",
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
        err(
            {
                "success": False,
                "code": "order_not_found",
                "message": "order does not exist",
            },
            status.HTTP_404_NOT_FOUND,
        )

    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "status": order.status,
        "total_items": order.total_items,
        "items": [
            {"sku": i.sku, "quantity": i.quantity}
            for i in order.items
        ],
    }
