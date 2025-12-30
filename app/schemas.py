from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, StrictStr, StrictInt


# =========================================================
# COMMON BASE
# =========================================================
class APIModel(BaseModel):
    model_config = {
        "from_attributes": True,  # enables orm_mode replacement in v2
    }


# =========================================================
# INVENTORY
# =========================================================
class InventoryItem(APIModel):
    sku: StrictStr = Field(..., min_length=1)
    name: StrictStr
    stock: StrictInt = Field(..., ge=0)


class InventoryUpdate(BaseModel):
    stock: StrictInt = Field(..., ge=0)


# =========================================================
# ORDER REQUEST
# =========================================================
class OrderItemRequest(BaseModel):
    sku: StrictStr = Field(..., min_length=1)
    qty: StrictInt = Field(..., gt=0)


class OrderRequest(BaseModel):
    customer_name: StrictStr = Field(..., min_length=1)
    items: List[OrderItemRequest] = Field(..., min_length=1)


# =========================================================
# ORDER RESPONSE (CREATE)
# =========================================================
class OrderResponse(APIModel):
    order_id: int
    status: str
    message: str


# =========================================================
# ORDER DETAIL (GET ORDER)
# =========================================================
class OrderItem(APIModel):
    sku: StrictStr
    quantity: StrictInt


class OrderDetail(APIModel):
    id: int
    customer_name: str
    status: str
    total_items: int
    items: List[OrderItem]


# =========================================================
# AUTH (OPTIONAL)
# =========================================================
class Token(APIModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None


class UserBase(APIModel):
    username: str
    role: str


class UserCreate(BaseModel):
    username: StrictStr = Field(..., min_length=3)
    password: StrictStr = Field(..., min_length=6)


class User(UserBase):
    id: int
    created_at: datetime
