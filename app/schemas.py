from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, StrictStr, StrictInt, conint


# =========================================================
# COMMON BASE
# =========================================================
class APIModel(BaseModel):
    model_config = {"from_attributes": True}  # orm_mode replacement


# =========================================================
# INVENTORY SCHEMAS
# =========================================================
class InventoryItem(APIModel):
    sku: StrictStr
    name: StrictStr
    stock: StrictInt = Field(ge=0)


class StockUpdate(BaseModel):
    stock: conint(ge=0)


class InventoryPublic(BaseModel):
    sku: str
    name: str
    stock: int
    status: Literal["available", "few_left", "out_of_stock"]
    few_left: bool = False


# =========================================================
# ORDER REQUEST
# =========================================================
class OrderItemCreate(BaseModel):
    sku: StrictStr = Field(..., min_length=1)
    qty: StrictInt = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer_name: StrictStr = Field(..., min_length=1)
    items: List[OrderItemCreate] = Field(..., min_length=1)


# =========================================================
# ORDER RESPONSE (CREATE)
# =========================================================
class FulfilledItem(BaseModel):
    sku: str
    requested_qty: int
    fulfilled_qty: int
    remaining_stock: int
    few_left: bool


class OrderResponse(BaseModel):
    success: bool
    order_id: int
    status: Literal["confirmed"]
    fulfilment_status: Literal["fully fulfilled", "partially fulfilled"]
    partial_fulfilment: bool
    items: List[FulfilledItem]
    message: str


# =========================================================
# ORDER DETAIL (GET ORDER)
# =========================================================
class OrderItem(APIModel):
    sku: str
    quantity: int


class OrderDetail(APIModel):
    id: int
    customer_name: str
    status: str
    total_items: int
    items: List[OrderItem]


# =========================================================
# USER / AUTH (OPTIONAL)
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
