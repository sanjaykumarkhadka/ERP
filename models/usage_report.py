from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from database import db

class UsageReport(db.Model):
    __tablename__ = 'usage_report_table'

    id = Column(Integer, primary_key=True)
    week_commencing = Column(Date)
    production_date = Column(Date, nullable=False)
    recipe_code = Column(String(50), nullable=False)
    raw_material = Column(String(255), nullable=False)  # This column DOES exist
    usage_kg = Column(Float, nullable=False)  # This column DOES exist
    percentage = Column(Float, nullable=False)
    created_at = Column(DateTime)

    def __repr__(self):
        return f'<UsageReport {self.raw_material} - {self.production_date}>'