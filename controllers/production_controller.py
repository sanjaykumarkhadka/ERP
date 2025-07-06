from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime, timedelta
from database import db  
from models.production import Production
from models.filling import Filling
from models.item_master import ItemMaster
from models.packing import Packing
from sqlalchemy.sql import text
import openpyxl
from io import BytesIO

production_bp = Blueprint('production', __name__, template_folder='templates')

@production_bp.route('/production_list', methods=['GET'])
def production_list():
    # Get search parameters from query string
    search_production_code = request.args.get('production_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    search_production_date_start = request.args.get('production_date_start', '').strip()
    search_production_date_end = request.args.get('production_date_end', '').strip()

    # Query productions with optional filters
    productions_query = Production.query
    if search_week_commencing:
        try:
            week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
            productions_query = productions_query.filter(Production.week_commencing == week_commencing_date)
        except ValueError:
            flash("Invalid Week Commencing date format.", 'error')
    
    # Handle date range filter
    if search_production_date_start or search_production_date_end:
        try:
            if search_production_date_start:
                start_date = datetime.strptime(search_production_date_start, '%Y-%m-%d').date()
                productions_query = productions_query.filter(Production.production_date >= start_date)
            if search_production_date_end:
                end_date = datetime.strptime(search_production_date_end, '%Y-%m-%d').date()
                productions_query = productions_query.filter(Production.production_date <= end_date)
                
            # Validate date range if both dates are provided
            if search_production_date_start and search_production_date_end:
                if start_date > end_date:
                    flash("Start date must be before or equal to end date.", 'error')
                    return render_template('production/list.html', 
                                        productions=[],
                                        search_production_code=search_production_code,
                                        search_description=search_description,
                                        search_week_commencing=search_week_commencing,
                                        search_production_date_start=search_production_date_start,
                                        search_production_date_end=search_production_date_end,
                                        current_page="production")
        except ValueError:
            flash("Invalid date format.", 'error')

    if search_production_code:
        productions_query = productions_query.filter(Production.production_code == search_production_code)
    
    if search_description:
        productions_query = productions_query.filter(Production.description.ilike(f"%{search_description}%"))

    # Get all productions for the filtered criteria
    productions = productions_query.all()

    # Calculate total based on filtered productions
    total_kg = 0.0
    recipe_family_totals = {}
    for production in productions:
        if production.total_kg is not None:
            # Get recipe family code (before the dot)
            recipe_family = production.production_code.split('.')[0] if '.' in production.production_code else production.production_code
            
            # Initialize recipe family total if not exists
            if recipe_family not in recipe_family_totals:
                recipe_family_totals[recipe_family] = 0.0
            
            # Add to recipe family total
            recipe_family_totals[recipe_family] += production.total_kg
            total_kg += production.total_kg

    return render_template('production/list.html',
                         productions=productions,
                         search_production_code=search_production_code,
                         search_description=search_description,
                         search_week_commencing=search_week_commencing,
                         search_production_date_start=search_production_date_start,
                         search_production_date_end=search_production_date_end,
                         total_kg=total_kg,
                         recipe_family_totals=recipe_family_totals,
                         current_page="production")

@production_bp.route('/production_create', methods=['GET', 'POST'])
def production_create():
    # Get recipe family and packing ID from query parameters
    recipe_family = request.args.get('recipe_family')
    packing_id = request.args.get('packing_id')
    
    # If we have a packing ID, get the packing entry to pre-fill dates
    packing_entry = None
    if packing_id:
        packing_entry = Packing.query.get(packing_id)
    
    if request.method == 'POST':
        try:
            production_date_str = request.form['production_date']
            production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
            production_code = request.form['production_code']
            product_description = request.form['product_description']
            
            # Calculate week commencing (Monday of the production date) 
            def get_week_commencing(dt):
                return dt - timedelta(days=dt.weekday())
            week_commencing = get_week_commencing(production_date)

            # Validate production_code exists in Item Master as WIP
            wip_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                ItemMaster.item_code == production_code,
                ItemMaster.item_type.has(type_name='WIP')
            ).first()
            if not wip_item:
                flash(f"No WIP item found for production code {production_code}.", 'error')
                return render_template('production/create.html', 
                                    recipe_family=recipe_family,
                                    packing_entry=packing_entry,
                                    current_page="production")

            # Get total_kg from form
            total_kg = float(request.form['total_kg']) if request.form.get('total_kg') else 0.0
                
            # Calculate batches based on total_kg
            batch_size = 300.0  # Default batch size
            batches = total_kg / batch_size if total_kg > 0 else 0.0

            new_production = Production(
                production_date=production_date,
                item_id=wip_item.id,  # Use foreign key
                production_code=production_code,  # Keep for backward compatibility
                description=product_description,
                batches=batches,
                total_kg=total_kg,
                week_commencing=week_commencing 
            )
            db.session.add(new_production)
            db.session.commit()

            flash("Production entry created successfully!", "success")
            
            # If we have a packing ID, redirect back to the packing edit page
            if packing_id:
                return redirect(url_for('packing.packing_edit', id=packing_id))
            return redirect(url_for('production.production_list'))
            
        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('production/create.html', 
                                recipe_family=recipe_family,
                                packing_entry=packing_entry,
                                current_page="production")
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('production/create.html', 
                                recipe_family=recipe_family,
                                packing_entry=packing_entry,
                                current_page="production")

    return render_template('production/create.html', 
                         recipe_family=recipe_family,
                         packing_entry=packing_entry,
                         current_page="production")

@production_bp.route('/production_edit/<int:id>', methods=['GET', 'POST'])
def production_edit(id):
    production = Production.query.get_or_404(id)

    if request.method == 'POST':
        try:
            production_date_str = request.form['production_date']
            production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
            production_code = request.form['production_code']
            product_description = request.form['product_description']

            # Calculate week commencing (Monday of the production date)
            def get_monday_of_week(dt):
                return dt - timedelta(days=dt.weekday())
            week_commencing = get_monday_of_week(production_date)

            # Update item_id if production_code changed
            if production_code != (production.item.item_code if production.item else production.production_code):
                new_wip_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                    ItemMaster.item_code == production_code,
                    ItemMaster.item_type.has(type_name='WIP')
                ).first()
                if new_wip_item:
                    production.item_id = new_wip_item.id
                else:
                    flash(f"No WIP item found for production code {production_code}.", 'error')
                    return render_template('production/edit.html', production=production, current_page="production")

            # Update the production entry
            production.production_date = production_date
            production.production_code = production_code
            production.description = product_description
            production.week_commencing = week_commencing
            
            # Only update total_kg and batches if provided in form
            if 'total_kg' in request.form and request.form['total_kg']:
                production.total_kg = float(request.form['total_kg'])
                production.batches = production.total_kg / 300.0 if production.total_kg > 0 else 0.0

            db.session.commit()
            flash('Production updated successfully!', 'success')
            return redirect(url_for('production.production_list'))

        except ValueError as e:
            db.session.rollback()
            flash(f"Invalid input: {str(e)}. Please check your data.", 'error')
            return render_template('production/edit.html', production=production, current_page="production")
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", 'error')
            return render_template('production/edit.html', production=production, current_page="production")

    return render_template('production/edit.html', production=production, current_page="production")

@production_bp.route('/production_delete/<int:id>', methods=['POST'])
def production_delete(id):
    production = Production.query.get_or_404(id)
    try:
        db.session.delete(production)
        db.session.commit()
        flash("Production entry deleted successfully!", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"An unexpected error occurred: {str(e)}", 'error')
    return redirect(url_for('production.production_list'))



# Autocomplete for Production Code
@production_bp.route('/autocomplete_production', methods=['GET'])
def autocomplete_production():
    search = request.args.get('query', '').strip()

    if not search:
        return jsonify([])

    try:
        query = text("SELECT production_code, description FROM production WHERE production_code LIKE :search LIMIT 10")
        results = db.session.execute(query, {"search": f"{search}%"}).fetchall()
        suggestions = [{"production_code": row[0], "description": row[1]} for row in results]
        return jsonify(suggestions)
    except Exception as e:
        print("Error fetching production autocomplete suggestions:", e)
        return jsonify([])

# Search Productions via AJAX
@production_bp.route('/get_search_productions', methods=['GET'])
def get_search_productions():
    search_production_code = request.args.get('production_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    search_production_date_start = request.args.get('production_date_start', '').strip()
    search_production_date_end = request.args.get('production_date_end', '').strip()

    try:
        productions_query = Production.query

        if search_week_commencing:
            try:
                week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
                productions_query = productions_query.filter(Production.week_commencing == week_commencing_date)
            except ValueError:
                return jsonify({"error": "Invalid Week Commencing date format"}), 400

        # Handle date range filter
        if search_production_date_start or search_production_date_end:
            try:
                if search_production_date_start:
                    start_date = datetime.strptime(search_production_date_start, '%Y-%m-%d').date()
                    productions_query = productions_query.filter(Production.production_date >= start_date)
                if search_production_date_end:
                    end_date = datetime.strptime(search_production_date_end, '%Y-%m-%d').date()
                    productions_query = productions_query.filter(Production.production_date <= end_date)
            except ValueError:
                return jsonify({"error": "Invalid Production Date format"}), 400

        if search_production_code:
            productions_query = productions_query.filter(Production.production_code == search_production_code)

        if search_description:
            productions_query = productions_query.filter(Production.description.ilike(f"%{search_description}%"))

        # Get all productions for the filtered criteria
        productions = productions_query.all()

        # Calculate total based on production code
        total_kg = sum(p.total_kg for p in productions if p.total_kg is not None)

        productions_data = [
            {
                "id": production.id,
                "production_date": production.production_date.strftime('%Y-%m-%d') if production.production_date else "",
                "week_commencing": production.week_commencing.strftime('%Y-%m-%d') if production.week_commencing else "",
                "production_code": production.production_code or "",
                "description": production.description or "",
                "batches": production.batches if production.batches is not None else "",
                "total_kg": production.total_kg if production.total_kg is not None else ""
            }
            for production in productions
        ]

        return jsonify({
            "productions": productions_data,
            "total_kg": total_kg
        })
    except Exception as e:
        print("Error fetching search productions:", e)
        return jsonify({"error": "Failed to fetch production entries"}), 500


    
# Export Productions to Excel
@production_bp.route('/export_productions_excel', methods=['GET'])
def export_productions_excel():
    search_production_code = request.args.get('production_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    search_production_date_start = request.args.get('production_date_start', '').strip()
    search_production_date_end = request.args.get('production_date_end', '').strip()

    try:
        productions_query = Production.query

        if search_week_commencing:
            try:
                week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
                productions_query = productions_query.filter(Production.week_commencing == week_commencing_date)
            except ValueError:
                flash("Invalid Week Commencing date format.", 'error')
                return redirect(url_for('production.production_list'))

        # Handle date range filter
        if search_production_date_start or search_production_date_end:
            try:
                if search_production_date_start:
                    start_date = datetime.strptime(search_production_date_start, '%Y-%m-%d').date()
                    productions_query = productions_query.filter(Production.production_date >= start_date)
                if search_production_date_end:
                    end_date = datetime.strptime(search_production_date_end, '%Y-%m-%d').date()
                    productions_query = productions_query.filter(Production.production_date <= end_date)
                    
                # Validate date range if both dates are provided
                if search_production_date_start and search_production_date_end:
                    if start_date > end_date:
                        flash("Start date must be before or equal to end date.", 'error')
                        return redirect(url_for('production.production_list'))
            except ValueError:
                flash("Invalid Production Date format.", 'error')
                return redirect(url_for('production.production_list'))
        if search_production_code:
            productions_query = productions_query.filter(Production.production_code.ilike(f"%{search_production_code}%"))
        if search_description:
            productions_query = productions_query.filter(Production.description.ilike(f"%{search_description}%"))

        productions = productions_query.all()

        # Create a new workbook and select the active sheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Productions"

        # Define headers
        headers = ["ID", "Week Commencing", "Production Date", "Production Code", "Description", "Batches", "Total KG"]
        ws.append(headers)

        # Add data rows
        for production in productions:
            ws.append([
                production.id,
                production.week_commencing.strftime('%Y-%m-%d') if production.week_commencing else '',
                production.production_date.strftime('%Y-%m-%d') if production.production_date else '',
                production.production_code or '',
                production.description or '',
                production.batches if production.batches is not None else '',
                production.total_kg if production.total_kg is not None else ''
            ])

        # Create a BytesIO object to save the Excel file
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"productions_export_{timestamp}.xlsx"

        # Send the file as a downloadable attachment
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print("Error generating Excel file:", e)
        flash(f"Error generating Excel file: {str(e)}", 'error')
        return redirect(url_for('production.production_list'))

# Usage Report for Production (renamed to avoid conflict with recipe.usage)
@production_bp.route('/production_usage')
def production_usage():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Query to get production and recipe usage data using new schema
    from models.recipe_master import RecipeMaster
    from sqlalchemy.orm import aliased
    
    # Create aliases for ItemMaster to avoid conflicts
    ProductionItem = aliased(ItemMaster)
    ComponentItem = aliased(ItemMaster)
    
    query = db.session.query(
        Production,
        RecipeMaster,
        ComponentItem.description.label('component_name')
    ).join(
        ProductionItem, Production.item_id == ProductionItem.id  # Join Production to ItemMaster (WIP item)
    ).join(
        RecipeMaster, ProductionItem.id == RecipeMaster.recipe_wip_id  # Join to RecipeMaster via recipe_wip_id
    ).join(
        ComponentItem, RecipeMaster.component_item_id == ComponentItem.id  # Join to component ItemMaster
    )
    
    # Apply date filters if provided
    if from_date and to_date:
        query = query.filter(
            Production.production_date >= from_date,
            Production.production_date <= to_date
        )
    
    # Get the results
    usage_data = query.all()
    
    # Group data by production date
    grouped_usage_data = {}
    for production, recipe, component_name in usage_data:
        date = production.production_date  # production_date is already a date object
        # Calculate the Monday of the week for the production_date
        def get_monday_date(date_str):
            from datetime import datetime, timedelta
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            return date - timedelta(days=date.weekday())
        
        week_commencing = get_monday_date(date.strftime('%Y-%m-%d'))
        
        if date not in grouped_usage_data:
            grouped_usage_data[date] = []
            
        grouped_usage_data[date].append({
            'week_commencing': week_commencing.strftime('%Y-%m-%d'),
            'production_date': production.production_date.strftime('%Y-%m-%d'),
            'production_code': production.production_code,
            'recipe_code': production.item.item_code if production.item else 'Unknown',
            'component_material': component_name,
            'usage_kg': float(recipe.quantity_kg) * (production.batches or 0),  # Use quantity_kg and batches
            'kg_per_batch': float(recipe.quantity_kg),
            'percentage': 0.0  # Set to 0 since percentage is not used in new schema
        })
    
    return render_template('production/usage.html',
                         grouped_usage_data=grouped_usage_data,
                         from_date=from_date,
                         to_date=to_date,
                         current_page='production_usage')

# Raw Material Report for Production
@production_bp.route('/production_raw_material_report', methods=['GET'])
def production_raw_material_report():
    try:
        # Get week commencing filter from request
        week_commencing = request.args.get('week_commencing')
        
        # Base query for weekly data - using current schema with corrected field names
        raw_material_query = """
        SELECT 
            DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY) as week_commencing,
            component_im.description as component_material,
            component_im.id as component_item_id,
            SUM(p.total_kg * (r.quantity_kg / recipe_totals.total_recipe_kg) * 100) as total_usage
        FROM production p
        JOIN item_master production_im ON p.item_id = production_im.id
        JOIN recipe_master r ON production_im.id = r.recipe_wip_id
        JOIN item_master component_im ON r.component_item_id = component_im.id
        JOIN (
            SELECT 
                r2.recipe_wip_id,
                SUM(r2.quantity_kg) as total_recipe_kg
            FROM recipe_master r2
            GROUP BY r2.recipe_wip_id
        ) recipe_totals ON r.recipe_wip_id = recipe_totals.recipe_wip_id
        """
        
        # Add date filter to the query
        params = {}
        if week_commencing:
            raw_material_query += """ 
            WHERE DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY) = :week_commencing
            """
            params['week_commencing'] = datetime.strptime(week_commencing, '%Y-%m-%d').date()
        
        raw_material_query += """
        GROUP BY 
            DATE(p.production_date - INTERVAL (WEEKDAY(p.production_date)) DAY),
            component_im.description,
            component_im.id
        ORDER BY week_commencing DESC, component_im.description
        """
        
        results = db.session.execute(text(raw_material_query), params).fetchall()
        
        # Convert to list of dictionaries for template
        raw_material_data = [
            {
                'week_commencing': result.week_commencing.strftime('%d/%m/%Y'),
                'raw_material': result.component_material,
                'usage': round(float(result.total_usage), 2)
            }
            for result in results
        ]
        
        return render_template('production/raw_material_report.html', 
                             raw_material_data=raw_material_data,
                             week_commencing=week_commencing,
                             current_page='production_raw_material_report')
        
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return render_template('production/raw_material_report.html', 
                             raw_material_data=[],
                             week_commencing=week_commencing,
                             current_page='production_raw_material_report')