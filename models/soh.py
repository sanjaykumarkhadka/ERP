from database import db

class SOH(db.Model):
    __tablename__ = 'soh'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    week_commencing = db.Column(db.Date, nullable=True)
    
    # Foreign key to ItemMaster instead of fg_code string
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    machinery_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID', ondelete='SET NULL'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id', ondelete='SET NULL'), nullable=True)
    
    # Keep fg_code temporarily for migration compatibility (will be removed later)
    fg_code = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255))
    
    soh_dispatch_boxes = db.Column(db.Float, default=0.0)
    soh_dispatch_units = db.Column(db.Float, default=0.0)
    soh_packing_boxes = db.Column(db.Float, default=0.0)
    soh_packing_units = db.Column(db.Float, default=0.0)
    soh_total_boxes = db.Column(db.Float, default=0.0)
    soh_total_units = db.Column(db.Float, default=0.0)
    edit_date = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    item = db.relationship('ItemMaster', backref='soh_records')
    machinery = db.relationship('Machinery', backref='soh_records')
    department = db.relationship('Department', backref='soh_records')

    __table_args__ = (
        db.UniqueConstraint('week_commencing', 'item_id', name='uix_soh_week_commencing_item_id'),
        # Keep old constraint temporarily for migration
        db.Index('idx_soh_fg_code', 'fg_code'),
    )

    def __repr__(self):
        return f"<SOH {self.item.item_code if self.item else self.fg_code} - {self.week_commencing}>"