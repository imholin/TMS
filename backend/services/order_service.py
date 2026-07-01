"""
Order Service - Order creation, status management, fee calculation.
Uses SQLAlchemy models from backend.models.
"""
import hashlib
import random
import time
from datetime import datetime, timedelta
from typing import Optional, List

from backend.extensions import db
from backend.models.order import Order
from backend.models.user import User


class OrderService:
    """Service for managing express delivery orders."""

    STATUS_TRANSITIONS = {
        "pending": {"confirmed", "cancelled"},
        "confirmed": {"picked_up", "cancelled"},
        "picked_up": {"in_transit", "returned"},
        "in_transit": {"delivered", "returned"},
        "delivered": set(),
        "cancelled": set(),
        "returned": set(),
    }

    VALID_STATUSES = {"pending", "confirmed", "picked_up", "in_transit", "delivered", "cancelled", "returned"}

    @staticmethod
    def generate_order_no() -> str:
        """Generate 'ORD' + timestamp + 4 random digits."""
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        suffix = ''.join(random.choices('0123456789', k=4))
        return f"ORD{ts}{suffix}"

    @staticmethod
    def calculate_fee(weight: float, origin_city: str, dest_city: str) -> dict:
        """
        Fee breakdown:
        - First kg: 楼1.5
        - Additional: 楼0.8/kg
        - Distance proxy: MD5 city pair hash 鈫?楼5鈥?0
        """
        if weight <= 0:
            raise ValueError("Weight must be positive")

        first_kg_fee = 1.5
        additional_kg_fee = 0.8
        weight_fee = first_kg_fee + max(0, (weight - 1)) * additional_kg_fee

        pair = f"{origin_city}:{dest_city}"
        hash_val = int(hashlib.md5(pair.encode()).hexdigest(), 16)
        base_fee = 5.0 + (hash_val % 46)

        cod_fee = 0.0  # COD fee handled separately
        total = round(weight_fee + base_fee, 2)

        return {
            "origin_city": origin_city,
            "dest_city": dest_city,
            "weight": weight,
            "first_kg_fee": round(first_kg_fee, 2),
            "additional_kg_fee_per_kg": round(additional_kg_fee, 2),
            "weight_fee": round(weight_fee, 2),
            "distance_fee": round(base_fee, 2),
            "cod_fee": cod_fee,
            "total_fee": total,
        }

    @classmethod
    def create_order(cls, data: dict, user_id: str) -> Order:
        """Create order with status='pending', auto-calculated fee."""
        required = ["sender_name", "sender_phone", "sender_address", "sender_city",
                    "receiver_name", "receiver_phone", "receiver_address", "receiver_city",
                    "weight"]
        for field in required:
            if not data.get(field):
                raise ValueError(f"Missing required field: {field}")

        weight = float(data["weight"])
        if weight <= 0:
            raise ValueError("Weight must be positive")

        fee = cls.calculate_fee(weight, data["sender_city"], data["receiver_city"])

        order = Order(
            order_no=cls.generate_order_no(),
            sender_name=data["sender_name"],
            sender_phone=data["sender_phone"],
            sender_address=data["sender_address"],
            sender_city=data["sender_city"],
            sender_province=data.get("sender_province", ""),
            receiver_name=data["receiver_name"],
            receiver_phone=data["receiver_phone"],
            receiver_address=data["receiver_address"],
            receiver_city=data["receiver_city"],
            receiver_province=data.get("receiver_province", ""),
            weight=weight,
            volume=float(data.get("volume", 0)),
            description=data.get("description", ""),
            status="pending",
            payment_type=data.get("payment_type", "prepaid"),
            cod_amount=float(data.get("cod_amount", 0)),
            total_fee=fee["total_fee"],
            user_id=user_id,
        )

        db.session.add(order)
        db.session.commit()
        return order

    @classmethod
    def confirm_order(cls, order_id: str) -> Order:
        """Change status to 'confirmed'."""
        order = cls.get_order(order_id)
        if order.status != "pending":
            raise ValueError(f"Cannot confirm: order is '{order.status}'")
        order.status = "confirmed"
        db.session.commit()
        return order

    @classmethod
    def cancel_order(cls, order_id: str) -> Order:
        """Cancel order if not yet in transit or delivered."""
        order = cls.get_order(order_id)
        if order.status in ("in_transit", "delivered"):
            raise ValueError(f"Cannot cancel: order is '{order.status}'")
        order.status = "cancelled"
        db.session.commit()
        return order

    @classmethod
    def update_order_status(cls, order_id: str, new_status: str) -> Order:
        """Validate and apply status transition."""
        if new_status not in cls.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")
        order = cls.get_order(order_id)
        allowed = cls.STATUS_TRANSITIONS.get(order.status, set())
        if new_status not in allowed:
            raise ValueError(f"Transition '{order.status}' 鈫?'{new_status}' not allowed. Allowed: {allowed or 'none'}")
        order.status = new_status
        db.session.commit()
        return order

    @classmethod
    def get_order(cls, order_id: str) -> Order:
        """Get order by ID."""
        order = db.session.get(Order, order_id)
        if not order:
            raise KeyError(f"Order not found: {order_id}")
        return order

    @classmethod
    def get_orders(cls, filters: Optional[dict] = None) -> tuple:
        """Filter + paginate orders. Returns (items, total)."""
        filters = filters or {}
        query = Order.query

        if "status" in filters:
            query = query.filter(Order.status == filters["status"])
        if "sender_city" in filters:
            query = query.filter(Order.sender_city == filters["sender_city"])
        if "receiver_city" in filters:
            query = query.filter(Order.receiver_city == filters["receiver_city"])
        if "date_from" in filters:
            dt = datetime.strptime(filters["date_from"], "%Y-%m-%d")
            query = query.filter(Order.created_at >= dt)
        if "date_to" in filters:
            dt = datetime.strptime(filters["date_to"], "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Order.created_at < dt)

        query = query.order_by(Order.created_at.desc())
        total = query.count()
        page = int(filters.get("page", 1))
        per_page = int(filters.get("per_page", 20))
        per_page = min(per_page, 100)
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total
