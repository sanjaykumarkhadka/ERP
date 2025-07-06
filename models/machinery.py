from database import db

class Machinery(db.Model):
    __tablename__ = 'machinery'
    machineID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    machineryName = db.Column(db.String(50), nullable=False, unique=True)