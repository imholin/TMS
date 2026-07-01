"""
Billing Service - Expense management and financial reporting.
Uses SQLAlchemy models from backend.models.
"""
from datetime import datetime, date
from collections import defaultdict

from backend.extensions import db
from backend.models.expense import Expense


class BillingService:
    """Service for expense management and billing reports."""

    CATEGORIES = ['fuel', 'toll', 'driver_salary', 'maintenance', 'food', 'accommodation', 'other']

    @staticmethod
    def generate_expense_no() -> str:
        """Generate unique expense number: EXP+YYYYMMDDHHMMSS+4digits."""
        from backend.utils.helpers import generate_no
        no = generate_no('EXP')
        while Expense.query.filter_by(expense_no=no).first():
            no = generate_no('EXP')
        return no

    @staticmethod
    def record_expense(data: dict, user_id: str) -> Expense:
        """Record a new expense entry."""
        category = data.get('category', 'other')
        if category not in Expense.VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Valid: {Expense.VALID_CATEGORIES}")
        amount = float(data.get('amount', 0))
        if amount <= 0:
            raise ValueError("Expense amount must be positive")
        expense_no = data.get('expense_no') or BillingService.generate_expense_no()
        expense = Expense(
            expense_no=expense_no,
            category=category,
            amount=amount,
            description=data.get('description', ''),
            vehicle_id=data.get('vehicle_id'),
            driver_id=data.get('driver_id'),
            shipment_id=data.get('shipment_id'),
            user_id=user_id,
            receipt_url=data.get('receipt_url'),
            expense_date=data.get('expense_date', date.today()),
        )
        db.session.add(expense)
        db.session.commit()
        return expense

    @staticmethod
    def get_expenses_by_shipment(shipment_id: str) -> dict:
        """Return all expenses for a shipment with category summary."""
        expenses = Expense.query.filter_by(shipment_id=shipment_id).all()
        by_cat = defaultdict(float)
        for e in expenses:
            by_cat[e.category] += e.amount
        return {
            'shipment_id': shipment_id,
            'expenses': [e.to_dict() for e in expenses],
            'total': sum(e.amount for e in expenses),
            'by_category': dict(by_cat),
            'count': len(expenses),
        }

    @staticmethod
    def get_expenses_by_driver(driver_id: str, date_from: str = None, date_to: str = None) -> dict:
        """Return expenses for a driver within optional date range."""
        query = Expense.query.filter_by(driver_id=driver_id)
        if date_from:
            query = query.filter(Expense.expense_date >= date_from)
        if date_to:
            query = query.filter(Expense.expense_date <= date_to)
        expenses = query.order_by(Expense.expense_date.desc()).all()
        by_cat = defaultdict(float)
        for e in expenses:
            by_cat[e.category] += e.amount
        return {
            'driver_id': driver_id,
            'date_from': date_from,
            'date_to': date_to,
            'expenses': [e.to_dict() for e in expenses],
            'total': sum(e.amount for e in expenses),
            'by_category': dict(by_cat),
            'count': len(expenses),
        }

    @staticmethod
    def get_expenses_by_vehicle(vehicle_id: str, date_from: str = None, date_to: str = None) -> dict:
        """Return expenses for a vehicle within optional date range."""
        query = Expense.query.filter_by(vehicle_id=vehicle_id)
        if date_from:
            query = query.filter(Expense.expense_date >= date_from)
        if date_to:
            query = query.filter(Expense.expense_date <= date_to)
        expenses = query.order_by(Expense.expense_date.desc()).all()
        by_cat = defaultdict(float)
        for e in expenses:
            by_cat[e.category] += e.amount
        return {
            'vehicle_id': vehicle_id,
            'date_from': date_from,
            'date_to': date_to,
            'expenses': [e.to_dict() for e in expenses],
            'total': sum(e.amount for e in expenses),
            'by_category': dict(by_cat),
            'count': len(expenses),
        }

    @staticmethod
    def get_daily_summary(date_str: str) -> dict:
        """Daily expense summary grouped by category."""
        expenses = Expense.query.filter_by(expense_date=date_str).all()
        by_cat = defaultdict(lambda: {'count': 0, 'total': 0.0})
        for e in expenses:
            by_cat[e.category]['count'] += 1
            by_cat[e.category]['total'] += e.amount
        return {
            'date': date_str,
            'total': sum(e.amount for e in expenses),
            'count': len(expenses),
            'by_category': dict(by_cat),
            'expenses': [e.to_dict() for e in expenses],
        }

    @staticmethod
    def get_monthly_report(year: int, month: int) -> dict:
        """Monthly expense report: totals, by-category, by-driver, by-vehicle."""
        start = f'{year}-{month:02d}-01'
        if month == 12:
            end = f'{year + 1}-01-01'
        else:
            end = f'{year}-{month + 1:02d}-01'

        expenses = Expense.query.filter(
            Expense.expense_date >= start,
            Expense.expense_date < end,
        ).all()

        total = sum(e.amount for e in expenses)

        by_cat = defaultdict(lambda: {'count': 0, 'total': 0.0})
        for e in expenses:
            by_cat[e.category]['count'] += 1
            by_cat[e.category]['total'] += e.amount

        by_driver = defaultdict(float)
        for e in expenses:
            if e.driver_id:
                by_driver[e.driver_id] += e.amount

        by_vehicle = defaultdict(float)
        for e in expenses:
            if e.vehicle_id:
                by_vehicle[e.vehicle_id] += e.amount

        return {
            'year': year,
            'month': month,
            'total': total,
            'count': len(expenses),
            'by_category': dict(by_cat),
            'by_driver': dict(by_driver),
            'by_vehicle': dict(by_vehicle),
        }
