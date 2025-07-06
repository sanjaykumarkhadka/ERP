from database import db  

class Filling(db.Model):
    __tablename__ = 'filling'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    week_commencing = db.Column(db.Date, nullable=True)  # New column
    filling_date = db.Column(db.Date, nullable=False)
    
    # Foreign key to ItemMaster (references WIPF items)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    machinery_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID', ondelete='SET NULL'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id', ondelete='SET NULL'), nullable=True)
    
    # Filling-specific data
    kilo_per_size = db.Column(db.Float, default=0.0)

    # Relationships
    item = db.relationship('ItemMaster', backref='filling_records')
    machinery = db.relationship('Machinery', backref='filling_records')
    department = db.relationship('Department', backref='filling_records')

    def __repr__(self):
        return f"<Filling {self.item.item_code} - {self.filling_date}>"