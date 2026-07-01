from datetime import datetime
import uuid
import random

from backend.models.base import BaseModel
from backend.extensions import db


class Order(BaseModel):
    """Order model representing customer's delivery request."""
    __tablename__ = 'orders'
    
    # Order number (format: ORD+YYYYMMDDHHMMSS+random 4)
    order_no = db.Column(db.String(30), unique=True, nullable=False, index=True)
    
    # Sender information
    sender_name = db.Column(db.String(100), nullable=False)
    sender_phone = db.Column(db.String(20), nullable=False)
    sender_address = db.Column(db.Text, nullable=False)
    sender_city = db.Column(db.String(50), nullable=False)
    sender_province = db.Column(db.String(50), nullable=False)
    
    # Receiver information
    receiver_name = db.Column(db.String(100), nullable=False)
    receiver_phone = db.Column(db.String(20), nullable=False)
    receiver_address = db.Column(db.Text, nullable=False)
    receiver_city = db.Column(db.String(50), nullable=False)
    receiver_province = db.Column(db.String(50), nullable=False)
    
    # Package information
    weight = db.Column(db.Float, nullable=False)  # kg
    volume = db.Column(db.Float, nullable=False)  # cubic cm
    description = db.Column(db.Text, nullable=True)
    
    # Status and payment
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    payment_type = db.Column(db.String(20), nullable=False, default='prepaid')
    cod_amount = db.Column(db.Float, nullable=False, default=0.0)
    total_fee = db.Column(db.Float, nullable=False, default=0.0)
    
    # Foreign keys
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='orders')
    
    # Status constants
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PICKED_UP = 'picked_up'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_RETURNED = 'returned'
    
    VALID_STATUSES = [
        STATUS_PENDING, STATUS_CONFIRMED, STATUS_PICKED_UP, 
        STATUS_IN_TRANSIT, STATUS_DELIVERED, STATUS_CANCELLED, STATUS_RETURNED
    ]
    
    # Payment type constants
    PAYMENT_PREPAID = 'prepaid'
    PAYMENT_COD = 'cod'
    
    VALID_PAYMENT_TYPES = [PAYMENT_PREPAID, PAYMENT_COD]
    
    def __init__(self, **kwargs):
        """Initialize Order with auto-generated order_no."""
        super().__init__()
        if 'order_no' not in kwargs:
            kwargs['order_no'] = self._generate_order_no()
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @staticmethod
    def _generate_order_no() -> str:
        """Generate unique order number."""
        now = datetime.now().strftime('%Y%m%d%H%M%S')
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        return f"ORD{now}{random_digits}"
    
    def to_dict(self) -> dict:
        """Convert order to dictionary."""
        result = super().to_dict()
        result.update({
            'order_no': self.order_no,
            'sender_name': self.sender_name,
            'sender_phone': self.sender_phone,
            'sender_address': self.sender_address,
            'sender_city': self.sender_city,
            'sender_province': self.sender_province,
            'receiver_name': self.receiver_name,
            'receiver_phone': self.receiver_phone,
            'receiver_address': self.receiver_address,
            'receiver_city': self.receiver_city,
            'receiver_province': self.receiver_province,
            'weight': self.weight,
            'volume': self.volume,
            'description': self.description,
            'status': self.status,
            'payment_type': self.payment_type,
            'cod_amount': self.cod_amount,
            'total_fee': self.total_fee,
            'user_id': self.user_id
        })
        return result
    
    def __repr__(self) -> str:
        return f"<Order {self.order_no} ({self.status})>"
