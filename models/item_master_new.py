from database import db
from sqlalchemy import CheckConstraint

class ItemMaster(db.Model):
    __tablename__ = 'item_master'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    # Direct item type (no lookup table needed)
    item_type = db.Column(db.String(20), nullable=False)  # RM, WIP, WIPF, FG, Packaging
    
    # Basic attributes
    category = db.Column(db.String(100))
    department = db.Column(db.String(100))
    machinery = db.Column(db.String(100))
    min_stock = db.Column(db.Float)
    max_stock = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    price_per_kg = db.Column(db.Float)
    is_make_to_order = db.Column(db.Boolean, default=False)
    loss_percentage = db.Column(db.Float)
    calculation_factor = db.Column(db.Float)
    
    # Self-referencing foreign keys for FG composition
    wip_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
    wipf_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id'), nullable=True)
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Self-referencing relationships
    wip_item = db.relationship('ItemMaster', remote_side=[id], foreign_keys=[wip_item_id], backref='finished_goods_using_wip')
    wipf_item = db.relationship('ItemMaster', remote_side=[id], foreign_keys=[wipf_item_id], backref='finished_goods_using_wipf')
    
    # Recipe components relationships
    recipe_components = db.relationship('RecipeComponent', foreign_keys='RecipeComponent.wip_item_id', backref='wip_item')
    used_in_recipes = db.relationship('RecipeComponent', foreign_keys='RecipeComponent.rm_item_id', backref='raw_material_item')
    
    # Business rule constraints
    __table_args__ = (
        CheckConstraint(
            "(item_type = 'FG' AND wip_item_id IS NOT NULL) OR (item_type != 'FG' AND wip_item_id IS NULL AND wipf_item_id IS NULL)",
            name='chk_fg_composition'
        ),
        CheckConstraint(
            "item_type IN ('RM', 'WIP', 'WIPF', 'FG', 'Packaging')",
            name='chk_valid_item_type'
        ),
    )

    def __repr__(self):
        return f'<ItemMaster {self.item_code} - {self.description}>'
    
    # Item type property methods
    @property
    def is_raw_material(self):
        return self.item_type == 'RM'

    @property 
    def is_wip(self):
        return self.item_type == 'WIP'
        
    @property
    def is_wipf(self):
        return self.item_type == 'WIPF'
        
    @property
    def is_finished_good(self):
        return self.item_type == 'FG'
    
    @property
    def is_packaging(self):
        return self.item_type == 'Packaging'

    # Recipe and composition methods
    def get_recipe_components(self):
        """Get all raw materials used in this WIP's recipe"""
        if not self.is_wip:
            return []
        return [rc.raw_material_item for rc in self.recipe_components]

    def get_total_recipe_weight(self):
        """Get total weight of all components in this WIP's recipe"""
        if not self.is_wip:
            return 0
        return sum(rc.quantity_kg for rc in self.recipe_components)

    def get_finished_goods_using_this_wip(self):
        """Get all finished goods that use this WIP"""
        if not self.is_wip:
            return []
        return self.finished_goods_using_wip

    def get_finished_goods_using_this_wipf(self):
        """Get all finished goods that use this WIPF"""
        if not self.is_wipf:
            return []
        return self.finished_goods_using_wipf

    def get_complete_bom(self):
        """Get complete Bill of Materials for this item"""
        bom = {
            'item': self,
            'components': []
        }
        
        if self.is_finished_good:
            # FG composition
            if self.wip_item:
                wip_components = []
                for rc in self.wip_item.recipe_components:
                    wip_components.append({
                        'item': rc.raw_material_item,
                        'quantity_kg': rc.quantity_kg,
                        'level': 2,
                        'type': 'RM via WIP'
                    })
                
                bom['components'].append({
                    'item': self.wip_item,
                    'quantity_kg': 1.0,  # Assumed 1:1 ratio
                    'level': 1,
                    'type': 'WIP',
                    'sub_components': wip_components
                })
            
            if self.wipf_item:
                bom['components'].append({
                    'item': self.wipf_item,
                    'quantity_kg': 1.0,  # Assumed 1:1 ratio
                    'level': 1,
                    'type': 'WIPF'
                })
        
        elif self.is_wip:
            # WIP recipe components
            for rc in self.recipe_components:
                bom['components'].append({
                    'item': rc.raw_material_item,
                    'quantity_kg': rc.quantity_kg,
                    'level': 1,
                    'type': 'RM'
                })
        
        return bom

    def calculate_material_requirements(self, required_quantity=1.0):
        """Calculate raw material requirements for given quantity"""
        requirements = {}
        
        if self.is_finished_good and self.wip_item:
            # For FG, get requirements from its WIP
            for rc in self.wip_item.recipe_components:
                rm_code = rc.raw_material_item.item_code
                requirements[rm_code] = {
                    'item': rc.raw_material_item,
                    'quantity_needed': rc.quantity_kg * required_quantity,
                    'description': rc.raw_material_item.description
                }
        
        elif self.is_wip:
            # For WIP, get direct recipe requirements
            for rc in self.recipe_components:
                rm_code = rc.raw_material_item.item_code
                requirements[rm_code] = {
                    'item': rc.raw_material_item,
                    'quantity_needed': rc.quantity_kg * required_quantity,
                    'description': rc.raw_material_item.description
                }
        
        return requirements

    def get_production_flow_summary(self):
        """Get summary of this item's production flow"""
        if self.is_raw_material:
            return "Raw Material - Used in recipes"
        elif self.is_wip:
            component_count = len(self.recipe_components)
            fg_count = len(self.finished_goods_using_wip)
            return f"WIP - {component_count} components, used in {fg_count} finished goods"
        elif self.is_wipf:
            fg_count = len(self.finished_goods_using_wipf)
            return f"WIPF - Final processing step for {fg_count} finished goods"
        elif self.is_finished_good:
            flow = "FG"
            if self.wip_item:
                flow += f" - Uses WIP: {self.wip_item.item_code}"
            if self.wipf_item:
                flow += f" - Uses WIPF: {self.wipf_item.item_code}"
            return flow
        elif self.is_packaging:
            return "Packaging Material"
        else:
            return "Unknown item type"

class RecipeComponent(db.Model):
    __tablename__ = 'recipe_components'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # The WIP item being produced (recipe output)
    wip_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id', ondelete='CASCADE'), nullable=False)
    
    # The Raw Material component required (recipe input)
    rm_item_id = db.Column(db.Integer, db.ForeignKey('item_master.id', ondelete='CASCADE'), nullable=False)
    
    # Quantity of this RM needed to make the WIP
    quantity_kg = db.Column(db.Float, nullable=False)
    
    # Optional recipe metadata
    recipe_code = db.Column(db.String(50))
    step_order = db.Column(db.Integer, default=1)
    notes = db.Column(db.Text)
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('wip_item_id', 'rm_item_id', name='uix_wip_rm_component'),
        CheckConstraint('quantity_kg > 0', name='chk_positive_quantity'),
    )

    def __repr__(self):
        return f'<RecipeComponent: {self.rm_item_id} -> {self.wip_item_id} ({self.quantity_kg}kg)>'

    @property
    def percentage_of_recipe(self):
        """Calculate this component's percentage of total recipe weight"""
        if not self.wip_item:
            return 0
        total_weight = sum(rc.quantity_kg for rc in self.wip_item.recipe_components)
        return (self.quantity_kg / total_weight * 100) if total_weight > 0 else 0 