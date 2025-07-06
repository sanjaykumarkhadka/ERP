from database import db
from sqlalchemy.orm import relationship

class ItemMaster(db.Model):
    """
    Central table for all items in the system.
    Contains self-referencing relationships for FG composition.
    """
    __tablename__ = 'item_master'

    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=False)
    
    # Foreign Key to the ItemType lookup table
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    
    # Foreign keys for lookup tables - FIXED with correct column names
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id'), nullable=True)
    machinery_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID'), nullable=True)
    uom_id = db.Column(db.Integer, db.ForeignKey('uom_type.UOMID'), nullable=True)
    
    min_stock = db.Column(db.DECIMAL(10, 2), default=0.00)
    max_stock = db.Column(db.DECIMAL(10, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)
    price_per_kg = db.Column(db.DECIMAL(12, 4), nullable=True)
    price_per_uom = db.Column(db.DECIMAL(12, 4), nullable=True)
    is_make_to_order = db.Column(db.Boolean, default=False)
    loss_percentage = db.Column(db.DECIMAL(5, 2), default=0.00)
    calculation_factor = db.Column(db.DECIMAL(10, 4), default=1.0000)
    
    # Additional columns that might exist in database
    min_level = db.Column(db.DECIMAL(10, 2), nullable=True)
    max_level = db.Column(db.DECIMAL(10, 2), nullable=True)
    kg_per_unit = db.Column(db.DECIMAL(10, 4), nullable=True)
    units_per_bag = db.Column(db.DECIMAL(10, 2), nullable=True)
    avg_weight_per_unit = db.Column(db.DECIMAL(10, 4), nullable=True)
    supplier_name = db.Column(db.String(255), nullable=True)

    # Audit fields (added to resolve User model relationship errors)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # --- FG Composition (Self-referencing Foreign Keys) ---
    # These will only be populated for Finished Goods (FG)
    wip_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
    wipf_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)

    # --- Relationships ---

    # Link to the ItemType object
    item_type = relationship("ItemType", back_populates="items")
    
    # Lookup table relationships - FIXED with correct model references
    category = relationship("Category", foreign_keys=[category_id])
    department = relationship("Department", foreign_keys=[department_id])
    machinery = relationship("Machinery", foreign_keys=[machinery_id])
    uom = relationship("UOM", foreign_keys=[uom_id])
    
    # These relationships allow an FG to easily access its WIP and WIPF components
    # We specify foreign_keys and remote_side to resolve ambiguity for self-referencing relationships
    wip_component = relationship("ItemMaster", foreign_keys=[wip_item_id], remote_side=[id])
    wipf_component = relationship("ItemMaster", foreign_keys=[wipf_item_id], remote_side=[id])
    
    # --- Recipe Relationships ---
    
    # If this item is a WIP, this relationship gives a list of its recipe components
    # It links to all RecipeMaster entries where this item is the 'recipe_wip'
    components = relationship(
        'RecipeMaster', 
        foreign_keys='RecipeMaster.recipe_wip_id', 
        back_populates='recipe_wip', 
        cascade="all, delete-orphan"
    )

    # If this item is used as a component (RM or WIP), this relationship shows all the recipes it is used in
    # Added overlaps parameter to fix the warning
    used_in_recipes = relationship(
        'RecipeMaster', 
        foreign_keys='RecipeMaster.component_item_id',
        overlaps="component_item"
    )

    def __repr__(self):
        return f"<ItemMaster {self.item_code} ({self.description})>"


class ItemAllergen(db.Model):
    __tablename__ = 'item_allergen'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    allergen_id = db.Column(db.Integer, db.ForeignKey('allergen.allergens_id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('item_id', 'allergen_id', name='uix_item_allergen'),
    )
    