from database import db
from datetime import date

class RawMaterialStocktake(db.Model):
    __tablename__ = 'raw_material_stocktake'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    week_commencing = db.Column(db.Date, nullable=False)
    stocktake_type = db.Column(db.String(20), nullable=False)  # weekly, monthly, annual, obsolete
    user = db.Column(db.String(100), nullable=False)
    item_code = db.Column(db.String(20), db.ForeignKey('item_master.item_code'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    current_stock = db.Column(db.Float, nullable=False, default=0.0)
    order_quantity = db.Column(db.Float, nullable=False, default=0.0)
    price_uom = db.Column(db.Float, nullable=False, default=0.0)
    stock_value = db.Column(db.Float, nullable=False, default=0.0)
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationships
    item = db.relationship('ItemMaster', backref='stocktakes', foreign_keys=[item_code], primaryjoin="RawMaterialStocktake.item_code==ItemMaster.item_code")
    category = db.relationship('Category', backref='stocktakes', foreign_keys=[category_id])
    
    def __repr__(self):
        return f'<RawMaterialStocktake {self.item_code} - {self.week_commencing} - {self.stocktake_type}>'
    
    @property
    def week_commencing_str(self):
        """Return formatted week commencing date"""
        return self.week_commencing.strftime('%Y-%m-%d') if self.week_commencing else '' 