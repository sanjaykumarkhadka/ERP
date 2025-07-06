# models/inventory.py
from database import db
from datetime import datetime
from models.category import Category
from models.item_master import ItemMaster

class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    week_commencing = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    total_required = db.Column(db.Float, nullable=False)
    soh = db.Column(db.Float, nullable=False)
    monday = db.Column(db.Float, nullable=False)
    tuesday = db.Column(db.Float, nullable=False)
    wednesday = db.Column(db.Float, nullable=False)
    thursday = db.Column(db.Float, nullable=False)
    friday = db.Column(db.Float, nullable=False)
    monday2 = db.Column(db.Float, nullable=False)
    tuesday2 = db.Column(db.Float, nullable=False)
    wednesday2 = db.Column(db.Float, nullable=False)
    thursday2 = db.Column(db.Float, nullable=False)
    friday2 = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', backref='inventories')
    raw_material = db.relationship('ItemMaster', backref='inventories')

    @property
    def value_soh(self):
        return self.soh * self.price_per_kg

    @property
    def total_to_be_ordered(self):
        return (self.monday + self.tuesday + self.wednesday + self.thursday + self.friday) - self.soh

    @property
    def variance(self):
        return (self.monday2 + self.tuesday2 + self.wednesday2 + self.thursday2 + self.friday2) - self.total_to_be_ordered

    @property
    def value_to_be_ordered(self):
        return (self.monday2 + self.tuesday2 + self.wednesday2 + self.thursday2 + self.friday2) * self.price_per_kg