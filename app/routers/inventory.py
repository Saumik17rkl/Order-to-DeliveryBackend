from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from app.database import SessionLocal
from app import models, schemas


router = APIRouter(prefix="/inventory", tags=["Inventory"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def err(detail: dict, code: int):
    raise HTTPException(status_code=code, detail=detail)


# ==========================
#  LIST INVENTORY
# ==========================

@router.get("/", response_model=list[schemas.InventoryItem])
def list_inventory(request: Request, db: Session = Depends(get_db)):

    log = logger.bind(trace_id=getattr(request.state, "trace_id", None))

    log.info("fetching inventory list")

    items = db.query(models.Inventory).all()

    log.info(f"returned {len(items)} inventory records")

    return items


# ==========================
#  UPDATE STOCK
# ==========================

@router.patch("/{sku}", response_model=schemas.InventoryItem)
def update_stock(
    sku: str,
    payload: schemas.InventoryUpdate,
    request: Request,
    db: Session = Depends(get_db)
):

    log = logger.bind(trace_id=getattr(request.state, "trace_id", None))

    sku = sku.upper().strip()

    log.info(f"stock update request — sku={sku}, new_stock={payload.stock}")

    try:
        with db.begin():

            inv = (
                db.query(models.Inventory)
                .filter(models.Inventory.sku == sku)
                .with_for_update()
                .first()
            )

            if not inv:
                log.warning(f"sku not found — {sku}")
                err(
                    {
                        "success": False,
                        "code": "sku_not_found",
                        "message": "sku not found",
                        "sku": sku,
                    },
                    status.HTTP_404_NOT_FOUND,
                )

            if payload.stock < 0:
                log.warning(f"negative stock rejected — sku={sku}")
                err(
                    {
                        "success": False,
                        "code": "invalid_stock_value",
                        "message": "stock cannot be negative",
                        "sku": sku,
                    },
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            inv.stock = payload.stock
            db.add(inv)

            log.success(f"stock updated — sku={sku}, stock={inv.stock}")

            return inv

    except HTTPException:
        raise

    except SQLAlchemyError:
        log.exception(f"database error while updating sku={sku}")
        err(
            {
                "success": False,
                "code": "db_error",
                "message": "database failure",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
