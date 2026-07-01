"""
Tracking, TrackingEvent, and ShipmentException models.
Stores shipment tracking history and exception events.
"""
from datetime import datetime

from backend.models.base import BaseModel
from backend.extensions import db


class Tracking(BaseModel):
    """Tracking event linked to both a shipment and an individual order.

    Used by the orders API to expose per-order tracking history.
    """
    __tablename__ = 'tracking'

    order_id     = db.Column(db.String(36), db.ForeignKey('orders.id'),     nullable=False, index=True)
    shipment_id  = db.Column(db.String(36), db.ForeignKey('shipments.id'),  nullable=True,  index=True)
    event_type   = db.Column(db.String(50), nullable=False, index=True)
    event_description = db.Column(db.String(200), nullable=True)
    location     = db.Column(db.String(200), nullable=True)
    latitude     = db.Column(db.Float, nullable=True)
    longitude    = db.Column(db.Float, nullable=True)
    timestamp    = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    created_by   = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    def to_dict(self) -> dict:
        result = super().to_dict()
        result.update({
            'order_id':         self.order_id,
            'shipment_id':      self.shipment_id,
            'event_type':       self.event_type,
            'event_description': self.event_description,
            'location':         self.location,
            'latitude':         self.latitude,
            'longitude':        self.longitude,
            'timestamp':        self.timestamp.isoformat() if self.timestamp else None,
            'created_by':       self.created_by,
        })
        return result

    def __repr__(self) -> str:
        return f"<Tracking {self.event_type} order={self.order_id}>"


class TrackingEvent(BaseModel):
    """Tracking event for a shipment."""
    __tablename__ = 'tracking_events'

    shipment_id = db.Column(db.String(36), db.ForeignKey('shipments.id'), nullable=False, index=True)
    event_type = db.Column(db.String(30), nullable=False, index=True)
    location = db.Column(db.String(200), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    operator = db.Column(db.String(100), nullable=True)
    event_time = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)

    EVENT_TYPES = [
        'departed', 'arrived', 'in_transit', 'picked_up',
        'delivered', 'exception', 'returned', 'custom'
    ]

    def to_dict(self) -> dict:
        result = super().to_dict()
        result.update({
            'shipment_id': self.shipment_id,
            'event_type': self.event_type,
            'location': self.location,
            'description': self.description,
            'operator': self.operator,
            'event_time': self.event_time.isoformat() if self.event_time else None,
        })
        return result

    def __repr__(self) -> str:
        return f"<TrackingEvent {self.event_type} @ {self.location}>"


class ShipmentException(BaseModel):
    """Exception events for shipments (damage, loss, delay, refused)."""
    __tablename__ = 'shipment_exceptions'

    shipment_id = db.Column(db.String(36), db.ForeignKey('shipments.id'), nullable=False, index=True)
    exception_type = db.Column(db.String(30), nullable=False)  # damage/loss/delay/refused
    description = db.Column(db.String(500), nullable=True)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=True)
    resolved = db.Column(db.String(10), default='no')  # no/yes/partially
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)

    EXCEPTION_TYPES = ['damage', 'loss', 'delay', 'refused', 'other']

    def to_dict(self) -> dict:
        result = super().to_dict()
        result.update({
            'shipment_id': self.shipment_id,
            'exception_type': self.exception_type,
            'description': self.description,
            'order_id': self.order_id,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
        })
        return result

    def __repr__(self) -> str:
        return f"<ShipmentException {self.exception_type} on {self.shipment_id}>"
