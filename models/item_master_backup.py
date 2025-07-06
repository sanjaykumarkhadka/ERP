from database import db

class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False)  # e.g., RM001, 2006, 2006.56, 2006.1
    description = db.Column(db.String(255))
    
    # Foreign key to ItemType table
    item_type_id = db.Column(db.Integer, db.ForeignKey('item_type.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.department_id'), nullable=True)
    machinery_id = db.Column(db.Integer, db.ForeignKey('machinery.machineID', ondelete='SET NULL'), nullable=True)
    uom_id = db.Column(db.Integer, db.ForeignKey('uom_type.UOMID'), nullable=True)  # Unit of Measure (kg, unit, box)
    
    # Item Attributes (previously scattered, now centralized)
    min_level = db.Column(db.Float)
    max_level = db.Column(db.Float)
    price_per_kg = db.Column(db.Float)  # For raw materials
    price_per_uom = db.Column(db.Float)  # Price per unit of measure
    kg_per_unit = db.Column(db.Float)   # For WIPF/FG
    units_per_bag = db.Column(db.Float)  # For FG
    avg_weight_per_unit = db.Column(db.Float)  # Average weight per unit in kg
    loss_percentage = db.Column(db.Float)  # Production/Filling loss
    supplier_name = db.Column(db.String(255))  # Name of the supplier for this item
    is_make_to_order = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    fw = db.Column(db.Boolean, default=False) 
    calculation_factor = db.Column(db.Float) 
    
    # User tracking fields
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    item_type = db.relationship('ItemType', backref='items')
    category = db.relationship('Category', backref='items')
    department = db.relationship('Department', backref='items')
    machinery = db.relationship('Machinery', backref='items')
    uom = db.relationship('UOM', backref='items')
    allergens = db.relationship('Allergen', secondary='item_allergen', backref='items')

    # Recipe relationships
    recipes_where_raw_material = db.relationship('RecipeMaster', 
                                               foreign_keys='RecipeMaster.raw_material_id',
                                               primaryjoin='ItemMaster.id == RecipeMaster.raw_material_id')
    
    recipes_where_finished_good = db.relationship('RecipeMaster',
                                                foreign_keys='RecipeMaster.finished_good_id',
                                                primaryjoin='ItemMaster.id == RecipeMaster.finished_good_id')

    def __repr__(self):
        return f'<ItemMaster {self.item_code} - {self.description}>'
    
    @property
    def is_raw_material(self):
        return self.item_type_id == 1  # Assuming item_type_id 1 is for raw materials

    @property 
    def is_wip(self):
        return self.item_type_id == 2  # Assuming item_type_id 2 is for WIP

    # ... etc for other types

    def get_recipe_components(self):
        """Get all components needed to make this item"""
        return [recipe.component_item for recipe in self.recipes_where_raw_material if recipe.is_active]

class ItemAllergen(db.Model):
    __tablename__ = 'item_allergen'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=False)
    allergen_id = db.Column(db.Integer, db.ForeignKey('allergen.allergens_id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('item_id', 'allergen_id', name='uix_item_allergen'),
    )
    