from datetime import datetime, date
from typing import Optional

from backend.models.base import BaseModel
from backend.extensions import db


class Vehicle(BaseModel):
    """Vehicle model for delivery vehicles."""
    __tablename__ = 'vehicles'
    
    # Basic information
    plate_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    vehicle_type = db.Column(db.String(20), nullable=False)
    brand = db.Column(db.String(50), nullable=True)
    model = db.Column(db.String(50), nullable=True)
    
    # Capacity
    load_capacity = db.Column(db.Float, nullable=False)  # kg
    volume_capacity = db.Column(db.Float, nullable=False, default=0.0)  # cubic m
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='available', index=True)
    
    # Assignment
    current_driver_id = db.Column(
        db.String(36),
        db.ForeignKey('drivers.id', use_alter=True),
        nullable=True
    )
    
    # Dates
    purchase_date = db.Column(db.Date, nullable=True)
    insurance_expire_date = db.Column(db.Date, nullable=True)
    annual_inspection_date = db.Column(db.Date, nullable=True)
    
    # Fuel information
    fuel_type = db.Column(db.String(20), nullable=False, default='gasoline')
    fuel_consumption = db.Column(db.Float, nullable=True)  # L/100km
    
    # Mileage
    mileage = db.Column(db.Float, nullable=False, default=0.0)  # km
    
    # Relationships
    shipments = db.relationship('Shipment', back_populates='vehicle', lazy='dynamic')
    expenses = db.relationship('Expense', back_populates='vehicle', lazy='dynamic')
    current_driver = db.relationship('Driver', back_populates='assigned_vehicle', foreign_keys=[current_driver_id])
    
    # Vehicle type constants
    TYPE_VAN = 'van'
    TYPE_MINI_VAN = 'mini_van'
    TYPE_TRUCK = 'truck'
    TYPE_LARGE_TRUCK = 'large_truck'
    
    VALID_VEHICLE_TYPES = [TYPE_VAN, TYPE_MINI_VAN, TYPE_TRUCK, TYPE_LARGE_TRUCK]
    
    # Status constants
    STATUS_AVAILABLE = 'available'
    STATUS_ON_DELIVERY = 'on_delivery'
    STATUS_MAINTENANCE = 'maintenance'
    STATUS_RETIRED = 'retired'
    
    VALID_STATUSES = [STATUS_AVAILABLE, STATUS_ON_DELIVERY, STATUS_MAINTENANCE, STATUS_RETIRED]
    
    # Fuel type constants
    FUEL_GASOLINE = 'gasoline'
    FUEL_DIESEL = 'diesel'
    FUEL_ELECTRIC = 'electric'
    
    VALID_FUEL_TYPES = [FUEL_GASOLINE, FUEL_DIESEL, FUEL_ELECTRIC]
    
    def __repr__(self) -> str:
        return f"<Vehicle {self.plate_no} ({self.vehicle_type})>"
    
    def to_dict(self) -> dict:
        """Convert vehicle to dictionary."""
        result = super().to_dict()
        result.update({
            'plate_no': self.plate_no,
            'vehicle_type': self.vehicle_type,
            'brand': self.brand,
            'model': self.model,
            'load_capacity': self.load_capacity,
            'volume_capacity': self.volume_capacity,
            'status': self.status,
            'current_driver_id': self.current_driver_id,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'insurance_expire_date': self.insurance_expire_date.isoformat() if self.insurance_expire_date else None,
            'annual_inspection_date': self.annual_inspection_date.isoformat() if self.annual_inspection_date else None,
            'fuel_type': self.fuel_type,
            'fuel_consumption': self.fuel_consumption,
            'mileage': self.mileage
        })
        return result
