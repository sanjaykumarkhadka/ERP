from database import db 

class Production(db.Model):
    __tablename__ = 'production'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    week_commencing = db.Column(db.Date, nullable=True)  # New column
    production_date = db.Column(db.Date, nullable=False)
    
    # Foreign key to ItemMaster instead of production_code string (references WIP items)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    machinery_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID', ondelete='SET NULL'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id', ondelete='SET NULL'), nullable=True)
    
    # Keep production_code temporarily for migration compatibility (will be removed later)
    production_code = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255))
    batches = db.Column(db.Float, default=0.0)
    total_kg = db.Column(db.Float, default=0.0)

    # Relationships
    item = db.relationship('ItemMaster', backref='production_records')
    machinery = db.relationship('Machinery', backref='production_records')
    department = db.relationship('Department', backref='production_records')

    def __repr__(self):
        return f"<Production {self.item.item_code if self.item else self.production_code} - {self.production_date}>"