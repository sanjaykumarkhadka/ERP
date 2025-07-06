from database import db

class Allergen(db.Model):
    __tablename__ = 'allergen'
    allergens_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<Allergen {self.name}>"