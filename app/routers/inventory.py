from fastapi import APIRouter, Depends, HTTPException, status, Request
from loguru import logger
from typing import List

from app.mongo import get_mongo_db
from app import schemas


router = APIRouter(prefix="/inventory", tags=["inventory"])


def normalize_sku(sku: str) -> str:
    return sku.strip().upper()


def err(detail: dict, code: int):
    raise HTTPException(status_code=code, detail=detail)


def get_db():
    return get_mongo_db()


def stock_flags(stock: int):
    stock = max(stock, 0)

    return {
        "few_left": stock > 0 and stock < 10,
        "out_of_stock": stock == 0,
        "status": (
            "out_of_stock" if stock == 0
            else "few_left" if stock < 10
            else "available"
        ),
        "stock": stock
    }


# ==========================
# LIST INVENTORY
# ==========================

@router.get("/", response_model=List[schemas.InventoryPublic])
def list_inventory(request: Request, db=Depends(get_db)):
    trace = getattr(request.state, "trace_id", None)
    log = logger.bind(trace_id=trace)

    log.info("fetching inventory list")

    docs = list(
        db["inventory"].find(
            {},
            {"_id": 0, "sku": 1, "name": 1, "stock": 1},
        )
    )

    result = []
    for item in docs:
        flags = stock_flags(item.get("stock", 0))

        result.append(
            {
                "sku": item["sku"],
                "name": item["name"],
                **flags,
            }
        )

    log.info(f"returned {len(result)} inventory records")
    return result


# ==========================
# GET SINGLE ITEM
# ==========================

@router.get("/{sku}", response_model=schemas.InventoryPublic)
def get_item(sku: str, request: Request, db=Depends(get_db)):
    trace = getattr(request.state, "trace_id", None)
    log = logger.bind(trace_id=trace)

    sku = normalize_sku(sku)
    log.info(f"fetch inventory item — {sku}")

    item = db["inventory"].find_one(
        {"sku": sku},
        {"_id": 0, "sku": 1, "name": 1, "stock": 1},
    )

    if not item:
        err(
            {
                "success": False,
                "code": "sku_not_found",
                "message": "sku not found",
                "sku": sku,
            },
            status.HTTP_404_NOT_FOUND,
        )

    flags = stock_flags(item["stock"])

    return {
        "sku": item["sku"],
        "name": item["name"],
        **flags,
    }


# ==========================
# UPDATE STOCK
# ==========================

@router.patch("/{sku}", response_model=schemas.InventoryPublic)
def update_stock(sku: str, payload: schemas.StockUpdate,
                 request: Request, db=Depends(get_db)):

    trace = getattr(request.state, "trace_id", None)
    log = logger.bind(trace_id=trace)

    sku = normalize_sku(sku)
    log.info(f"stock update request — sku={sku}, new_stock={payload.delta}")

    if payload.delta < 0:
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
        res = db["inventory"].update_one(
            {"sku": sku},
            {"$inc": {"stock": payload.delta}},
        )

        if res.matched_count == 0:
            err(
                {
                    "success": False,
                    "code": "sku_not_found",
                    "message": "sku not found",
                    "sku": sku,
                },
                status.HTTP_404_NOT_FOUND,
            )

        item = db["inventory"].find_one(
            {"sku": sku},
            {"_id": 0, "sku": 1, "name": 1, "stock": 1},
        )

        flags = stock_flags(item["stock"])

        log.success(f"stock updated — sku={sku}, stock={flags['stock']}")

        return {
            "sku": item["sku"],
            "name": item["name"],
            **flags,
        }

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
