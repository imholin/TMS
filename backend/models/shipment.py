# -*- coding: utf-8 -*-
"""Shipment model and ShipmentOrder association."""
from datetime import datetime
import random

from backend.models.base import BaseModel
from backend.extensions import db


# Association table: links shipments to orders (many-to-many via this table)
shipment_order_links = db.Table(
    'shipment_order_links',
    db.Column('shipment_id', db.String(36), db.ForeignKey('shipments.id'), primary_key=True),
    db.Column('order_id', db.String(36), db.ForeignKey('orders.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.now),
)


class Shipment(BaseModel):
    """Shipment: a vehicle-load unit containing one or more orders."""
    __tablename__ = 'shipments'

    shipment_no = db.Column(db.String(30), unique=True, nullable=False, index=True)
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id'), nullable=True)
    driver_id = db.Column(db.String(36), db.ForeignKey('drivers.id'), nullable=True)
    route_id = db.Column(db.String(36), db.ForeignKey('routes.id'), nullable=True)

    def __init__(self, **kwargs):
        super().__init__()
        if 'shipment_no' not in kwargs:
            kwargs['shipment_no'] = self._generate_shipment_no()
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def _generate_shipment_no() -> str:
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        return f"SHP{ts}{suffix}"

    departure_time = db.Column(db.DateTime, nullable=True)
    arrival_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='prepared', index=True)

    actual_distance = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Many-to-many with Order via shipment_order_links table
    orders = db.relationship(
        'Order', secondary=shipment_order_links,
        backref=db.backref('shipments', lazy='dynamic'),
        lazy='dynamic',
    )

    # Many-to-one relationships
    vehicle = db.relationship('Vehicle', back_populates='shipments')
    driver = db.relationship('Driver', back_populates='shipments')
    route = db.relationship('Route', back_populates='shipments')
    expenses = db.relationship('Expense', back_populates='shipment', lazy='select', viewonly=True)

    VALID_STATUSES = ['prepared', 'in_transit', 'delivered', 'cancelled']

    def to_dict(self) -> dict:
        result = super().to_dict()
        result.update({
            'shipment_no': self.shipment_no,
            'vehicle_id': self.vehicle_id,
            'driver_id': self.driver_id,
            'route_id': self.route_id,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'status': self.status,
            'actual_distance': self.actual_distance,
            'notes': self.notes,
            'order_count': self.orders.count() if hasattr(self.orders, 'count') else len(self.orders.all()),
        })
        return result

    def __repr__(self) -> str:
        return f'<Shipment {self.shipment_no} ({self.status})>'


class ShipmentOrder(BaseModel):
    """Extra metadata linking a shipment to an order (delivery status, etc.)."""
    __tablename__ = 'shipment_orders'

    shipment_id = db.Column(db.String(36), db.ForeignKey('shipments.id'), nullable=False, index=True)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False, index=True)
    delivery_status = db.Column(db.String(20), default='pending')
    delivery_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self) -> dict:
        result = super().to_dict()
        result.update({
            'shipment_id': self.shipment_id,
            'order_id': self.order_id,
            'delivery_status': self.delivery_status,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'notes': self.notes,
        })
        return result

    def __repr__(self) -> str:
        return f'<ShipmentOrder {self.shipment_id}-{self.order_id}>'
