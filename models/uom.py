from database import db

class UOM(db.Model):
    __tablename__ = 'uom_type'
    UOMID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UOMName = db.Column(db.String(50), nullable=False)
