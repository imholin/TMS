from datetime import datetime
from typing import Optional

from werkzeug.security import generate_password_hash, check_password_hash

from backend.models.base import BaseModel
from backend.extensions import db


class User(BaseModel):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    role = db.Column(db.String(20), nullable=False, default='operator')
    is_active = db.Column(db.String(20), nullable=False, default='active')
    
    # Relationships
    driver = db.relationship('Driver', back_populates='user', uselist=False, cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='user', lazy='dynamic')
    expenses = db.relationship('Expense', back_populates='user', lazy='dynamic')
    
    # Role constants
    ROLE_ADMIN = 'admin'
    ROLE_OPERATOR = 'operator'
    ROLE_DRIVER = 'driver'
    
    # Status constants
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    
    VALID_ROLES = [ROLE_ADMIN, ROLE_OPERATOR, ROLE_DRIVER]
    VALID_STATUSES = [STATUS_ACTIVE, STATUS_INACTIVE]
    
    def __init__(self, username: str, password: str, email: Optional[str] = None, 
                 role: str = 'operator', is_active: str = 'active'):
        """Initialize User instance."""
        super().__init__()
        self.username = username
        self.set_password(password)
        self.email = email
        self.role = role if role in self.VALID_ROLES else self.ROLE_OPERATOR
        self.is_active = is_active if is_active in self.VALID_STATUSES else self.STATUS_ACTIVE
    
    def set_password(self, password: str) -> None:
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches hash."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == self.ROLE_ADMIN
    
    @property
    def is_driver(self) -> bool:
        """Check if user is driver."""
        return self.role == self.ROLE_DRIVER
    
    @property
    def is_operator(self) -> bool:
        """Check if user is operator."""
        return self.role == self.ROLE_OPERATOR
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (exclude password_hash)."""
        result = super().to_dict()
        result.update({
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'driver_id': self.driver.id if self.driver else None
        })
        return result
    
    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
