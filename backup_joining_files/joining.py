from database import db
from datetime import datetime

class Joining(db.Model):
    __tablename__ = 'joining'
    
    id = db.Column(db.Integer, primary_key=True)
    fg_code = db.Column(db.String(50), nullable=False, index=True)
    fg_description = db.Column(db.String(255))
    filling_code = db.Column(db.String(50), index=True)
    filling_code_description = db.Column(db.String(255))
    production_code = db.Column(db.String(50), index=True)
    production_description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationships to ensure data integrity
    fg_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    filling_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
    production_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
    
    # Relationships
    fg_item = db.relationship('ItemMaster', foreign_keys=[fg_item_id], backref='joining_as_fg')
    filling_item = db.relationship('ItemMaster', foreign_keys=[filling_item_id], backref='joining_as_filling')
    production_item = db.relationship('ItemMaster', foreign_keys=[production_item_id], backref='joining_as_production')
    
    def __repr__(self):
        return f'<Joining {self.fg_code} → {self.filling_code} → {self.production_code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'fg_code': self.fg_code,
            'fg_description': self.fg_description,
            'filling_code': self.filling_code,
            'filling_code_description': self.filling_code_description,
            'production_code': self.production_code,
            'production_description': self.production_description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_hierarchy_for_fg(fg_code):
        """Get the complete hierarchy for a finished good"""
        return Joining.query.filter_by(fg_code=fg_code, is_active=True).first()
    
    @staticmethod
    def get_all_fg_hierarchies():
        """Get all active FG hierarchies"""
        return Joining.query.filter_by(is_active=True).all()
    
    @staticmethod
    def get_downstream_items(fg_code):
        """Get WIPF and WIP items for a given FG"""
        joining = Joining.get_hierarchy_for_fg(fg_code)
        if joining:
            return {
                'filling_code': joining.filling_code,
                'production_code': joining.production_code
            }
        return None
    
    def get_manufacturing_flow_type(self):
        """Determine the manufacturing flow type based on available components"""
        if self.filling_code and self.production_code:
            return "Complex flow (RM → WIP → WIPF → FG)"
        elif self.filling_code:
            return "Filling flow (RM → WIPF → FG)"
        elif self.production_code:
            return "Production flow (RM → WIP → FG)"
        else:
            return "Direct production (RM → FG)" 