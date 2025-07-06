from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz
from database import db

sydney_tz = pytz.timezone('Australia/Sydney')

def sydney_now():
    """Return current datetime in Sydney timezone"""
    return datetime.now(pytz.UTC).astimezone(sydney_tz)

class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # New columns
    department_id = Column(Integer, ForeignKey('department.department_id', ondelete='SET NULL'), nullable=True)
    mobile = Column(String(20), nullable=True)
    start_date = Column(Date, nullable=True)
    
    # Timestamps using Sydney timezone
    created_at = Column(DateTime, default=sydney_now)
    updated_at = Column(DateTime, default=sydney_now, onupdate=sydney_now)
    last_login = Column(DateTime)
    
    # Relationships
    department = relationship('Department', backref='users')
    created_items = relationship('ItemMaster', backref='created_by', foreign_keys='ItemMaster.created_by_id')
    updated_items = relationship('ItemMaster', backref='updated_by', foreign_keys='ItemMaster.updated_by_id')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>' 