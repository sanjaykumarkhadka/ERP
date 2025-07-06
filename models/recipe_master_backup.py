from database import db
from sqlalchemy import event

class RecipeMaster(db.Model):
    __tablename__ = 'recipe_master'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # The item being produced/assembled (e.g., Frankfurter WIP, WIPF, or Finished Good)
    finished_good_id = db.Column(db.Integer, db.ForeignKey('item_master.id', ondelete='CASCADE'), nullable=False)
    
    # A component needed to produce the assembly (e.g., Raw Material, WIP, or WIPF)
    raw_material_id = db.Column(db.Integer, db.ForeignKey('item_master.id', ondelete='CASCADE'), nullable=False)
    
    # How much of the component is needed to make one "unit" or "batch" of the assembly
    kg_per_batch = db.Column(db.Float, nullable=False)
    
    # Percentage of this component in the total recipe (calculated field)
    percentage = db.Column(db.Float)
    
    # Optional: UOM for the quantity if different units are mixed
    quantity_uom_id = db.Column(db.Integer, db.ForeignKey('uom_type.UOMID'), nullable=True)
    
    # Metadata
    recipe_code = db.Column(db.String(100))  # Optional grouping identifier
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Prevent duplicate component-assembly pairs
    __table_args__ = (
        db.UniqueConstraint('finished_good_id', 'raw_material_id', name='uix_finished_raw_material'),
    )

    # Relationships with ItemMaster
    finished_good_item = db.relationship('ItemMaster', foreign_keys=[finished_good_id])
    raw_material_item = db.relationship('ItemMaster', foreign_keys=[raw_material_id])

    def __repr__(self):
        return f'<Recipe: {self.raw_material_item.item_code} -> {self.finished_good_item.item_code}>'

    @classmethod
    def check_duplicate_materials(cls, finished_good_id, raw_material_id):
        """Check if this raw material is already used in this recipe"""
        existing = cls.query.filter_by(
            finished_good_id=finished_good_id,
            raw_material_id=raw_material_id
        ).first()
        return existing is not None

# Move these outside the class
@event.listens_for(RecipeMaster, 'before_insert')
@event.listens_for(RecipeMaster, 'before_update')
def validate_recipe_logic(mapper, connection, target):
    if target.check_duplicate_materials(target.finished_good_id, target.raw_material_id):
        pass 