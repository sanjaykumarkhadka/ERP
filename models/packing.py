from sqlalchemy import UniqueConstraint, ForeignKeyConstraint
from database import db
from datetime import date

class Packing(db.Model):
    __tablename__ = 'packing'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    week_commencing = db.Column(db.Date, nullable=True)  # Matches DEFAULT NULL
    packing_date = db.Column(db.Date, nullable=False)
    
    # Foreign key to ItemMaster
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    machinery_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID', ondelete='SET NULL'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id', ondelete='SET NULL'), nullable=True)
    
    special_order_kg = db.Column(db.Float, default=0.0, nullable=True)
    special_order_unit = db.Column(db.Integer, default=0, nullable=True)
    requirement_kg = db.Column(db.Float, default=0.0, nullable=True)
    requirement_unit = db.Column(db.Integer, default=0, nullable=True)
    avg_weight_per_unit = db.Column(db.Float, default=0.0, nullable=True)
    soh_requirement_kg_week = db.Column(db.Float, default=0.0, nullable=True)
    soh_requirement_units_week = db.Column(db.Integer, default=0, nullable=True)
    soh_kg = db.Column(db.Float, default=0.0, nullable=True)
    soh_units = db.Column(db.Float, default=0.0, nullable=True)
    total_stock_kg = db.Column(db.Float, default=0.0, nullable=True)
    total_stock_units = db.Column(db.Integer, default=0, nullable=True)
    calculation_factor = db.Column(db.Float, default=0.0, nullable=True)
    priority = db.Column(db.Integer, default=0, nullable=True)

    # Relationships
    item = db.relationship('ItemMaster', backref='packing_records')
    machinery = db.relationship('Machinery', backref='packing_records')
    department = db.relationship('Department', backref='packing_records')

    __table_args__ = (
        UniqueConstraint(
            'week_commencing', 'item_id', 'packing_date', 'machinery_id',
            name='uq_packing_week_item_date_machinery'
        ),
    )

    def __repr__(self):
        return f"<Packing {self.item.item_code} - {self.packing_date}>"