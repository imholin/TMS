from datetime import datetime
import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from backend.extensions import db


class BaseModel(db.Model):
    """Abstract base model with common fields."""
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def save(self):
        """Save the model instance to the database."""
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        """Delete the model instance from the database."""
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs):
        """Update model attributes and save."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_id(cls, id: str):
        """Get model instance by ID."""
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls):
        """Get all model instances."""
        return cls.query.all()
