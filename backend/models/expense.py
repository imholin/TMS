from datetime import datetime, date
import random

from backend.models.base import BaseModel
from backend.extensions import db


class Expense(BaseModel):
    """Expense model for tracking various expenses."""
    __tablename__ = 'expenses'
    
    # Expense number (format: EXP+YYYYMMDD+4 digits)
    expense_no = db.Column(db.String(30), unique=True, nullable=False, index=True)
    
    # Expense information
    category = db.Column(db.String(30), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Foreign keys (all nullable as expenses may not be linked to all)
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id'), nullable=True)
    driver_id = db.Column(db.String(36), db.ForeignKey('drivers.id'), nullable=True)
    shipment_id = db.Column(db.String(36), db.ForeignKey('shipments.id'), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Receipt
    receipt_url = db.Column(db.String(500), nullable=True)
    
    # Expense date
    expense_date = db.Column(db.Date, nullable=False, default=date.today)
    
    # Relationships
    vehicle = db.relationship('Vehicle', back_populates='expenses')
    driver = db.relationship('Driver', back_populates='expenses')
    shipment = db.relationship('Shipment', back_populates='expenses', lazy='select')
    user = db.relationship('User', back_populates='expenses')
    
    # Category constants
    CATEGORY_FUEL = 'fuel'
    CATEGORY_TOLL = 'toll'
    CATEGORY_DRIVER_SALARY = 'driver_salary'
    CATEGORY_MAINTENANCE = 'maintenance'
    CATEGORY_FOOD = 'food'
    CATEGORY_ACCOMMODATION = 'accommodation'
    CATEGORY_OTHER = 'other'
    
    VALID_CATEGORIES = [
        CATEGORY_FUEL, CATEGORY_TOLL, CATEGORY_DRIVER_SALARY,
        CATEGORY_MAINTENANCE, CATEGORY_FOOD, CATEGORY_ACCOMMODATION,
        CATEGORY_OTHER
    ]
    
    def __init__(self, **kwargs):
        """Initialize Expense with auto-generated expense_no."""
        super().__init__()
        if 'expense_no' not in kwargs:
            kwargs['expense_no'] = self._generate_expense_no()
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @staticmethod
    def _generate_expense_no() -> str:
        """Generate unique expense number."""
        now = datetime.now().strftime('%Y%m%d')
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        return f"EXP{now}{random_digits}"
    
    def to_dict(self) -> dict:
        """Convert expense to dictionary."""
        result = super().to_dict()
        result.update({
            'expense_no': self.expense_no,
            'category': self.category,
            'amount': self.amount,
            'description': self.description,
            'vehicle_id': self.vehicle_id,
            'driver_id': self.driver_id,
            'shipment_id': self.shipment_id,
            'user_id': self.user_id,
            'receipt_url': self.receipt_url,
            'expense_date': self.expense_date.isoformat() if self.expense_date else None
        })
        return result
    
    def __repr__(self) -> str:
        return f"<Expense {self.expense_no}: {self.category} - {self.amount}>"
