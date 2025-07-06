from database import db
from sqlalchemy.orm import relationship

class ItemType(db.Model):
    __tablename__ = 'item_type'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_name = db.Column(db.String(50), nullable=False, unique=True)                

    # Relationship to ItemMaster - this was missing and causing the error
    items = relationship("ItemMaster", back_populates="item_type")

    def __repr__(self):
        return f'<ItemType {self.type_name}>'