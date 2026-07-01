from datetime import datetime, date
from typing import Optional

from backend.models.base import BaseModel
from backend.extensions import db


class Driver(BaseModel):
    """Driver model for delivery drivers."""
    __tablename__ = 'drivers'
    
    # Personal information
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, index=True)
    id_card_no = db.Column(db.String(18), unique=True, nullable=True)
    
    # License information
    license_no = db.Column(db.String(50), unique=True, nullable=False)
    license_type = db.Column(db.String(5), nullable=False)  # A/B/C
    license_expire_date = db.Column(db.Date, nullable=False)
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='active', index=True)
    
    # Account linkage
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, unique=True)
    
    # Vehicle assignment
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id'), nullable=True)
    
    # Employment information
    hire_date = db.Column(db.Date, nullable=False, default=date.today)
    salary_type = db.Column(db.String(20), nullable=False, default='monthly')
    base_salary = db.Column(db.Float, nullable=False, default=0.0)
    
    # Relationships
    user = db.relationship('User', back_populates='driver', uselist=False)
    shipments = db.relationship('Shipment', back_populates='driver', lazy='dynamic')
    expenses = db.relationship('Expense', back_populates='driver', lazy='dynamic')
    assigned_vehicle = db.relationship('Vehicle', back_populates='current_driver', foreign_keys='Vehicle.current_driver_id')
    
    # Status constants
    STATUS_ACTIVE = 'active'
    STATUS_ON_DUTY = 'on_duty'
    STATUS_ON_LEAVE = 'on_leave'
    STATUS_SUSPENDED = 'suspended'
    
    VALID_STATUSES = [STATUS_ACTIVE, STATUS_ON_DUTY, STATUS_ON_LEAVE, STATUS_SUSPENDED]
    
    # License type constants
    LICENSE_A = 'A'
    LICENSE_B = 'B'
    LICENSE_C = 'C'
    
    VALID_LICENSE_TYPES = [LICENSE_A, LICENSE_B, LICENSE_C]
    
    # Salary type constants
    SALARY_MONTHLY = 'monthly'
    SALARY_TRIP_BASED = 'trip_based'
    
    VALID_SALARY_TYPES = [SALARY_MONTHLY, SALARY_TRIP_BASED]
    
    def __repr__(self) -> str:
        return f"<Driver {self.name} ({self.license_no})>"
    
    @property
    def is_license_expired(self) -> bool:
        """Check if driver's license is expired."""
        return date.today() > self.license_expire_date
    
    @property
    def license_days_remaining(self) -> int:
        """Calculate days until license expires."""
        return (self.license_expire_date - date.today()).days
    
    def to_dict(self) -> dict:
        """Convert driver to dictionary."""
        result = super().to_dict()
        result.update({
            'name': self.name,
            'phone': self.phone,
            'id_card_no': self.id_card_no,
            'license_no': self.license_no,
            'license_type': self.license_type,
            'license_expire_date': self.license_expire_date.isoformat() if self.license_expire_date else None,
            'status': self.status,
            'user_id': self.user_id,
            'vehicle_id': self.vehicle_id,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'salary_type': self.salary_type,
            'base_salary': self.base_salary,
            'is_license_expired': self.is_license_expired,
            'license_days_remaining': self.license_days_remaining
        })
        return result
