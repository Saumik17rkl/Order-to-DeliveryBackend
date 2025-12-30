from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum as SAEnum,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ENUM — ORDER STATUS
class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


# USERS  (optional but supports auth properly)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # user | admin
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"



# INVENTORY
class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)

    # force lowercase storage but allow input normalization in routes
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<Inventory sku={self.sku} stock={self.stock}>"


# ORDERS
class Orders(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255), nullable=False)

    status = Column(
        SAEnum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.PENDING,
    )

    total_items = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship(
        "OrderItems",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def __repr__(self):
        return f"<Order id={self.id} status={self.status}>"


# ORDER ITEMS
class OrderItems(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)

    sku = Column(String(50), nullable=False, index=True)

    quantity = Column(Integer, nullable=False)

    order = relationship("Orders", back_populates="items")

    def __repr__(self):
        return (
            f"<OrderItems order_id={self.order_id} sku={self.sku} qty={self.quantity}>"
        )


# INDEXES (PERFORMANCE — GOOD CHOICE)
Index("idx_inventory_sku", Inventory.sku)
Index("idx_order_items_sku", OrderItems.sku)
Index("idx_order_items_order_id", OrderItems.order_id)
