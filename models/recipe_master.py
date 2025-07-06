from database import db
from sqlalchemy.orm import relationship

class RecipeMaster(db.Model):
    """
    Recipe Master table for defining Bill of Materials.
    Currently uses the old database structure with mapped fields.
    """
    __tablename__ = 'recipe_master'

    id = db.Column(db.Integer, primary_key=True)
    
    # Map current database columns to what controller expects
    quantity_kg = db.Column(db.DECIMAL(10, 4), nullable=False)  # Maps to kg_per_batch
    recipe_wip_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)  # Maps to finished_good_id
    component_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)  # Maps to raw_material_id
    
    # Properties to map old database fields to what controller expects
    @property
    def kg_per_batch(self):
        """Map quantity_kg to kg_per_batch for controller compatibility."""
        return float(self.quantity_kg) if self.quantity_kg else 0.0
    
    @kg_per_batch.setter
    def kg_per_batch(self, value):
        self.quantity_kg = value
    
    @property
    def finished_good_id(self):
        """Map recipe_wip_id to finished_good_id for controller compatibility."""
        return self.recipe_wip_id
    
    @finished_good_id.setter
    def finished_good_id(self, value):
        self.recipe_wip_id = value
        
    @property
    def raw_material_id(self):
        """Map component_item_id to raw_material_id for controller compatibility."""
        return self.component_item_id
    
    @raw_material_id.setter  
    def raw_material_id(self, value):
        self.component_item_id = value
    
    @property
    def recipe_code(self):
        """Generate recipe_code from the finished good item code."""
        if hasattr(self, '_recipe_wip_item') and self._recipe_wip_item:
            return self._recipe_wip_item.item_code
        return "Unknown"
    
    @recipe_code.setter
    def recipe_code(self, value):
        # For now, ignore setting recipe_code as it's derived
        pass
        
    @property
    def description(self):
        """Generate description from the finished good item description."""
        if hasattr(self, '_recipe_wip_item') and self._recipe_wip_item:
            return self._recipe_wip_item.description
        return "Unknown"
    
    @description.setter
    def description(self, value):
        # For now, ignore setting description as it's derived
        pass
        
    @property
    def percentage(self):
        """Calculate percentage (placeholder for now)."""
        return 0.0
    
    @percentage.setter
    def percentage(self, value):
        # For now, ignore setting percentage
        pass
        
    @property
    def quantity_uom_id(self):
        """Placeholder for UOM ID."""
        return None

    # --- Relationships ---

    # Links back to the ItemMaster object that represents the WIP recipe (finished good)
    recipe_wip = relationship(
        'ItemMaster', 
        foreign_keys=[recipe_wip_id], 
        back_populates='components'
    )
    
    # Component item relationship
    component_item = relationship(
        'ItemMaster', 
        foreign_keys=[component_item_id]
    )

    # Ensure a component can only be added once to a specific recipe
    __table_args__ = (
        db.UniqueConstraint('recipe_wip_id', 'component_item_id', name='uq_recipe_component'),
    )

    def __repr__(self):
        return f"<RecipeMaster {self.recipe_code} uses {self.kg_per_batch}kg of component>"