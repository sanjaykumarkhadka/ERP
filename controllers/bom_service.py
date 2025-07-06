"""
BOM (Bill of Materials) Explosion Service
Handles automatic creation of downstream production requirements
Uses existing RecipeMaster model with current field names
"""
from app import db
from models.packing import Packing
from models.filling import Filling  
from models.production import Production
from models.item_master import ItemMaster
from models.recipe_master import RecipeMaster
from models.item_type import ItemType
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

def update_downstream_requirements(packing_date, week_commencing):
    """
    Aggregates all packing requirements for a given day and updates/creates
    the corresponding Filling and Production plans. This is the "Recipe Explosion".
    
    Args:
        packing_date: Date for which to calculate requirements
        week_commencing: Week commencing date for planning period
    """
    try:
        logger.info(f"Starting recipe explosion for {packing_date}, week {week_commencing}")
        
        # Step 1: Aggregate all packing requirements for the day by item
        daily_packing_reqs = db.session.query(
            Packing.item_id,
            func.sum(Packing.requirement_kg).label('total_req_kg')
        ).filter(
            Packing.packing_date == packing_date,
            Packing.week_commencing == week_commencing,
            Packing.requirement_kg > 0
        ).group_by(Packing.item_id).all()

        if not daily_packing_reqs:
            logger.info("No packing requirements found for the specified date")
            return True, "No packing requirements to process"

        # Dictionaries to hold aggregated needs
        filling_needs = {}  # {wipf_item_id: total_kg}
        production_needs = {}  # {wip_item_id: total_kg}

        def calculate_wip_requirements(item_id, required_kg, level=0):
            """
            Recursively calculate WIP requirements
            """
            if level > 10:  # Prevent infinite recursion
                logger.warning(f"Max recursion depth reached for item {item_id}")
                return
                
            # Get recipe components for this item using correct field names
            recipe_components = RecipeMaster.query.filter_by(
                recipe_wip_id=item_id  # Use correct field name
            ).join(ItemMaster, RecipeMaster.component_item_id == ItemMaster.id).all()
            
            for recipe in recipe_components:
                component_item = recipe.component_item
                if not component_item:
                    continue
                
                # Calculate needed quantity using the actual database field
                # quantity_kg represents the kg of component needed per batch
                needed_kg = required_kg  # Use 1:1 ratio since we're working with final quantities
                
                if needed_kg <= 0:
                    continue
                
                # Handle component based on type
                if component_item.item_type and component_item.item_type.type_name == 'WIPF':
                    filling_needs[component_item.id] = filling_needs.get(component_item.id, 0) + needed_kg
                    logger.info(f"WIPF requirement: {component_item.item_code} needs {needed_kg} kg")
                    
                elif component_item.item_type and component_item.item_type.type_name == 'WIP':
                    production_needs[component_item.id] = production_needs.get(component_item.id, 0) + needed_kg
                    logger.info(f"WIP requirement: {component_item.item_code} needs {needed_kg} kg")
                    # Recursively process this WIP's components
                    calculate_wip_requirements(component_item.id, needed_kg, level + 1)

        # Step 2: Process all packing requirements
        total_packing_kg = 0
        for packed_item_id, total_req_kg in daily_packing_reqs:
            total_packing_kg += total_req_kg
            logger.info(f"Processing recipes for item_id {packed_item_id}: {total_req_kg} kg required")
            calculate_wip_requirements(packed_item_id, total_req_kg)

        logger.info(f"Total packing requirement: {total_packing_kg} kg")

        # Step 3: Update Filling Table
        logger.info(f"Updating Filling requirements: {len(filling_needs)} items")
        
        # Delete existing entries for the day
        deleted_filling = Filling.query.filter_by(
            filling_date=packing_date, 
            week_commencing=week_commencing
        ).delete()
        logger.info(f"Deleted {deleted_filling} existing filling entries")
        
        filling_created = 0
        for item_id, total_kg in filling_needs.items():
            if total_kg > 0:
                new_filling = Filling(
                    filling_date=packing_date,
                    week_commencing=week_commencing,
                    item_id=item_id,
                    kilo_per_size=total_kg
                )
                db.session.add(new_filling)
                filling_created += 1
                
                item = ItemMaster.query.get(item_id)
                logger.info(f"Created filling entry: {item.item_code if item else item_id} - {total_kg} kg")

        # Step 4: Update Production Table
        logger.info(f"Updating Production requirements: {len(production_needs)} items")
        
        # Delete existing entries for the day
        deleted_production = Production.query.filter_by(
            production_date=packing_date, 
            week_commencing=week_commencing
        ).delete()
        logger.info(f"Deleted {deleted_production} existing production entries")
        
        production_created = 0
        total_production_kg = 0
        for item_id, total_kg in production_needs.items():
            if total_kg > 0:
                batches = total_kg / 300  # Using 300kg as standard batch size
                
                item = ItemMaster.query.get(item_id)
                if not item:
                    continue
                    
                production_code = item.item_code
                description = f"{item.item_code} - {item.description}"  # Include both code and description
                
                # Create production entry
                new_production = Production(
                    production_date=packing_date,
                    week_commencing=week_commencing,
                    item_id=item.id,
                    production_code=production_code,
                    description=description,
                    total_kg=total_kg,
                    batches=batches
                )
                db.session.add(new_production)
                production_created += 1
                total_production_kg += total_kg
                
                logger.info(f"Created production entry: {production_code} - {total_kg} kg ({batches} batches)")

        # Commit all changes
        db.session.commit()
        
        summary = (f"Recipe explosion completed: {filling_created} filling entries, "
                  f"{production_created} production entries created. "
                  f"Total packing: {total_packing_kg} kg, Total production: {total_production_kg} kg")
        logger.info(summary)
        return True, summary
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Recipe explosion failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

def get_recipe_summary(item_id):
    """Get a summary of all recipe components for an item"""
    try:
        item = ItemMaster.query.get(item_id)
        if not item:
            return None
            
        result = {
            'code': item.item_code,
            'description': item.description,
            'type': item.item_type.type_name if item.item_type else None,
            'components': []
        }
        
        recipes = RecipeMaster.query.filter_by(finished_good_id=item_id).all()
        for recipe in recipes:
            component_item = recipe.raw_material_item
            if component_item:
                result['components'].append({
                    'code': component_item.item_code,
                    'description': component_item.description,
                    'type': component_item.item_type.type_name if component_item.item_type else None,
                    'kg_per_batch': recipe.kg_per_batch,
                    'percentage': recipe.percentage
                })
                
        return result
    except Exception as e:
        logger.error(f"Error getting recipe summary: {str(e)}")
        return None

def calculate_component_requirements(item_id, required_kg):
    """
    Calculate all component requirements for a specific item and quantity
    Uses existing RecipeMaster structure with correct field names
    """
    try:
        requirements = {}
        
        # Get direct recipe components using correct field names
        recipe_components = RecipeMaster.query.filter_by(
            recipe_wip_id=item_id  # Use correct field name
        ).join(ItemMaster, RecipeMaster.component_item_id == ItemMaster.id).all()
        
        for recipe in recipe_components:
            component_item = recipe.component_item
            if not component_item:
                continue
            
            # Calculate requirement using actual database field
            needed_kg = required_kg * float(recipe.quantity_kg) if recipe.quantity_kg else 0
            
            if needed_kg > 0:
                requirements[component_item.item_code] = {
                    'item': component_item,
                    'total_kg': needed_kg,
                    'type': component_item.item_type.type_name if component_item.item_type else 'Unknown',
                    'recipe_quantity_kg': float(recipe.quantity_kg),
                    'recipe_percentage': 0.0  # Not calculated in this version
                }
        
        return requirements, "Success"
        
    except Exception as e:
        return None, f"Error calculating requirements: {str(e)}" 