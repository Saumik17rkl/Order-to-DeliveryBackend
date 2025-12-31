from fastapi import APIRouter, Depends, HTTPException, status, Request
from loguru import logger

from app.mongo import get_mongo_db
from app import schemas


router = APIRouter(prefix="/inventory", tags=["Inventory"])


def get_db():
    return get_mongo_db()


def err(detail: dict, code: int):
    raise HTTPException(status_code=code, detail=detail)


# ==========================
#  LIST INVENTORY
# ==========================

@router.get("/", response_model=list[schemas.InventoryItem])
def list_inventory(request: Request, db=Depends(get_db)):

    log = logger.bind(trace_id=getattr(request.state, "trace_id", None))

    log.info("fetching inventory list")

    items = list(db["inventory"].find({}, {"_id": 0, "sku": 1, "name": 1, "stock": 1}))

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
    db=Depends(get_db)
):

    log = logger.bind(trace_id=getattr(request.state, "trace_id", None))

    sku = sku.upper().strip()

    log.info(f"stock update request — sku={sku}, new_stock={payload.stock}")

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

    try:
        result = db["inventory"].update_one(
            {"sku": sku},
            {"$set": {"stock": payload.stock}},
        )

        if result.matched_count == 0:
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

        inv = db["inventory"].find_one({"sku": sku}, {"_id": 0, "sku": 1, "name": 1, "stock": 1})

        log.success(f"stock updated — sku={sku}, stock={inv['stock']}")
        return inv

    except HTTPException:
        raise

    except Exception:
        log.exception(f"database error while updating sku={sku}")
        err(
            {
                "success": False,
                "code": "db_error",
                "message": "database failure",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
