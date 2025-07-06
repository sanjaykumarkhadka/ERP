from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.joining import Joining
from models.item_master import ItemMaster
from database import db
from sqlalchemy import or_
import pandas as pd
import os

joining_bp = Blueprint('joining', __name__)

@joining_bp.route('/joining')
def list_joining():
    """Display all joining records with search and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    search = request.args.get('search', '')
    
    query = Joining.query
    
    if search:
        query = query.filter(
            or_(
                Joining.fg_code.contains(search),
                Joining.fg_description.contains(search),
                Joining.filling_code.contains(search),
                Joining.production_code.contains(search)
            )
        )
    
    joining_records = query.order_by(Joining.fg_code).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('joining/list.html', 
                         joining_records=joining_records,
                         search=search)

@joining_bp.route('/joining/upload-excel', methods=['POST'])
def upload_excel():
    """Upload and process Excel file to import joining data"""
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('joining.list_joining'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('joining.list_joining'))
        
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            flash('Please upload a valid Excel file (.xlsx, .xls)', 'error')
            return redirect(url_for('joining.list_joining'))
        
        # Save file temporarily
        filename = 'temp_joining_upload.xlsx'
        file.save(filename)
        
        try:
            # Read Excel file
            df = pd.read_excel(filename, sheet_name=0)  # First sheet
            df.columns = df.columns.str.strip()  # Clean column names
            
            print(f"Excel columns: {list(df.columns)}")
            
            # Expected columns: fg_code, filling_code, production, description
            # Or: FG Code, Filling Code, Production Code, Description
            column_mappings = {
                'fg_code': ['fg_code', 'FG Code', 'FG_Code'],
                'filling_code': ['filling_code', 'Filling Code', 'Filling_Code'],
                'production_code': ['production', 'Production Code', 'Production', 'production_code'],
                'description': ['description', 'Description', 'FG Description']
            }
            
            # Map columns
            mapped_columns = {}
            for target_col, possible_names in column_mappings.items():
                for possible_name in possible_names:
                    if possible_name in df.columns:
                        mapped_columns[target_col] = possible_name
                        break
            
            # Check if we have at least fg_code
            if 'fg_code' not in mapped_columns:
                flash('Excel file must contain FG Code column', 'error')
                return redirect(url_for('joining.list_joining'))
            
            created_count = 0
            updated_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    fg_code = str(row[mapped_columns['fg_code']]).strip()
                    if fg_code.lower() in ['nan', 'none', ''] or pd.isna(fg_code):
                        continue
                    
                    filling_code = None
                    if 'filling_code' in mapped_columns:
                        filling_val = row[mapped_columns['filling_code']]
                        if not pd.isna(filling_val) and str(filling_val).strip().lower() not in ['nan', 'none', '']:
                            filling_code = str(filling_val).strip()
                    
                    production_code = None
                    if 'production_code' in mapped_columns:
                        production_val = row[mapped_columns['production_code']]
                        if not pd.isna(production_val) and str(production_val).strip().lower() not in ['nan', 'none', '']:
                            production_code = str(production_val).strip()
                    
                    # Find FG item
                    fg_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                        ItemMaster.item_code == fg_code,
                        ItemMaster.item_type.has(type_name='FG')
                    ).first()
                    
                    if not fg_item:
                        errors.append(f"Row {index + 1}: FG item {fg_code} not found or not of type FG")
                        error_count += 1
                        continue
                    
                    # Find filling item if provided
                    filling_item = None
                    if filling_code:
                        filling_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                            ItemMaster.item_code == filling_code,
                            ItemMaster.item_type.has(type_name='WIPF')
                        ).first()
                        if not filling_item:
                            errors.append(f"Row {index + 1}: Filling item {filling_code} not found or not of type WIPF")
                            error_count += 1
                            continue
                    
                    # Find production item if provided
                    production_item = None
                    if production_code:
                        production_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                            ItemMaster.item_code == production_code,
                            ItemMaster.item_type.has(type_name='WIP')
                        ).first()
                        if not production_item:
                            errors.append(f"Row {index + 1}: Production item {production_code} not found or not of type WIP")
                            error_count += 1
                            continue
                    
                    # Check if joining record exists
                    existing = Joining.query.filter_by(fg_code=fg_code).first()
                    
                    if existing:
                        # Update existing record
                        existing.fg_description = fg_item.description
                        existing.filling_code = filling_code
                        existing.filling_code_description = filling_item.description if filling_item else None
                        existing.production_code = production_code
                        existing.production_description = production_item.description if production_item else None
                        existing.filling_item_id = filling_item.id if filling_item else None
                        existing.production_item_id = production_item.id if production_item else None
                        updated_count += 1
                    else:
                        # Create new record
                        joining = Joining(
                            fg_code=fg_code,
                            fg_description=fg_item.description,
                            filling_code=filling_code,
                            filling_code_description=filling_item.description if filling_item else None,
                            production_code=production_code,
                            production_description=production_item.description if production_item else None,
                            fg_item_id=fg_item.id,
                            filling_item_id=filling_item.id if filling_item else None,
                            production_item_id=production_item.id if production_item else None
                        )
                        db.session.add(joining)
                        created_count += 1
                    
                    # Commit in batches
                    if (index + 1) % 20 == 0:
                        db.session.commit()
                
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    error_count += 1
                    continue
            
            # Final commit
            db.session.commit()
            
            # Success message
            message_parts = []
            if created_count > 0:
                message_parts.append(f"{created_count} records created")
            if updated_count > 0:
                message_parts.append(f"{updated_count} records updated")
            if error_count > 0:
                message_parts.append(f"{error_count} errors")
            
            message = "Excel import completed: " + ", ".join(message_parts)
            
            if error_count > 0:
                flash(f"{message}. First few errors: {'; '.join(errors[:3])}", 'warning')
            else:
                flash(message, 'success')
            
        finally:
            # Clean up temp file
            if os.path.exists(filename):
                os.remove(filename)
                
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing Excel file: {str(e)}', 'error')
        if os.path.exists('temp_joining_upload.xlsx'):
            os.remove('temp_joining_upload.xlsx')
    
    return redirect(url_for('joining.list_joining'))

@joining_bp.route('/joining/create', methods=['GET', 'POST'])
def create_joining():
    """Create a new joining record"""
    if request.method == 'POST':
        try:
            fg_code = request.form.get('fg_code')
            filling_code = request.form.get('filling_code')
            production_code = request.form.get('production_code')
            
            # Validate FG item exists and is correct type using proper relationship query
            fg_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                ItemMaster.item_code == fg_code,
                ItemMaster.item_type.has(type_name='FG')
            ).first()
            if not fg_item:
                flash(f'Finished Good item {fg_code} not found or not of type FG', 'error')
                return render_template('joining/create.html')
            
            # Validate filling item if provided and is correct type
            filling_item = None
            if filling_code:
                filling_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                    ItemMaster.item_code == filling_code,
                    ItemMaster.item_type.has(type_name='WIPF')
                ).first()
                if not filling_item:
                    flash(f'Filling item {filling_code} not found or not of type WIPF', 'error')
                    return render_template('joining/create.html')
            
            # Validate production item if provided and is correct type
            production_item = None
            if production_code:
                production_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                    ItemMaster.item_code == production_code,
                    ItemMaster.item_type.has(type_name='WIP')
                ).first()
                if not production_item:
                    flash(f'Production item {production_code} not found or not of type WIP', 'error')
                    return render_template('joining/create.html')
            
            # Check if joining record already exists for this FG
            existing = Joining.query.filter_by(fg_code=fg_code).first()
            if existing:
                flash(f'Joining record already exists for FG {fg_code}', 'error')
                return render_template('joining/create.html')
            
            # Create new joining record
            joining = Joining(
                fg_code=fg_code,
                fg_description=fg_item.description,
                filling_code=filling_code,
                filling_code_description=filling_item.description if filling_item else None,
                production_code=production_code,
                production_description=production_item.description if production_item else None,
                fg_item_id=fg_item.id,
                filling_item_id=filling_item.id if filling_item else None,
                production_item_id=production_item.id if production_item else None
            )
            
            db.session.add(joining)
            db.session.commit()
            
            flash('Joining record created successfully!', 'success')
            return redirect(url_for('joining.list_joining'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating joining record: {str(e)}', 'error')
    
    return render_template('joining/create.html')

@joining_bp.route('/joining/edit/<int:id>', methods=['GET', 'POST'])
def edit_joining(id):
    """Edit an existing joining record"""
    joining = Joining.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            fg_code = request.form.get('fg_code')
            filling_code = request.form.get('filling_code')
            production_code = request.form.get('production_code')
            
            # Validate FG item exists and is correct type using proper relationship query
            fg_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                ItemMaster.item_code == fg_code,
                ItemMaster.item_type.has(type_name='FG')
            ).first()
            if not fg_item:
                flash(f'Finished Good item {fg_code} not found or not of type FG', 'error')
                return render_template('joining/edit.html', joining=joining)
            
            # Validate filling item if provided and is correct type
            filling_item = None
            if filling_code:
                filling_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                    ItemMaster.item_code == filling_code,
                    ItemMaster.item_type.has(type_name='WIPF')
                ).first()
                if not filling_item:
                    flash(f'Filling item {filling_code} not found or not of type WIPF', 'error')
                    return render_template('joining/edit.html', joining=joining)
            
            # Validate production item if provided and is correct type
            production_item = None
            if production_code:
                production_item = ItemMaster.query.join(ItemMaster.item_type).filter(
                    ItemMaster.item_code == production_code,
                    ItemMaster.item_type.has(type_name='WIP')
                ).first()
                if not production_item:
                    flash(f'Production item {production_code} not found or not of type WIP', 'error')
                    return render_template('joining/edit.html', joining=joining)
            
            # Check if another joining record exists for this FG (excluding current)
            existing = Joining.query.filter(
                Joining.fg_code == fg_code,
                Joining.id != id
            ).first()
            if existing:
                flash(f'Joining record already exists for FG {fg_code}', 'error')
                return render_template('joining/edit.html', joining=joining)
            
            # Update joining record
            joining.fg_code = fg_code
            joining.fg_description = fg_item.description
            joining.filling_code = filling_code
            joining.filling_code_description = filling_item.description if filling_item else None
            joining.production_code = production_code
            joining.production_description = production_item.description if production_item else None
            joining.fg_item_id = fg_item.id
            joining.filling_item_id = filling_item.id if filling_item else None
            joining.production_item_id = production_item.id if production_item else None
            joining.is_active = 'is_active' in request.form
            
            db.session.commit()
            
            flash('Joining record updated successfully!', 'success')
            return redirect(url_for('joining.list_joining'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating joining record: {str(e)}', 'error')
    
    return render_template('joining/edit.html', joining=joining)

@joining_bp.route('/joining/delete/<int:id>', methods=['POST'])
def delete_joining(id):
    """Delete a joining record"""
    try:
        joining = Joining.query.get_or_404(id)
        db.session.delete(joining)
        db.session.commit()
        flash('Joining record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting joining record: {str(e)}', 'error')
    
    return redirect(url_for('joining.list_joining'))

@joining_bp.route('/api/joining/search')
def search_joining():
    """API endpoint for searching joining records"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    joining_records = Joining.query.filter(
        or_(
            Joining.fg_code.contains(query),
            Joining.fg_description.contains(query),
            Joining.filling_code.contains(query),
            Joining.production_code.contains(query)
        )
    ).limit(10).all()
    
    return jsonify([record.to_dict() for record in joining_records])

@joining_bp.route('/api/joining/hierarchy/<fg_code>')
def get_hierarchy(fg_code):
    """API endpoint to get hierarchy for a specific FG code"""
    joining = Joining.get_hierarchy_for_fg(fg_code)
    if joining:
        return jsonify(joining.to_dict())
    return jsonify({'error': 'Hierarchy not found'}), 404

@joining_bp.route('/api/joining/validate-item')
def validate_item():
    """API endpoint to validate if an item code exists with proper type filtering"""
    item_code = request.args.get('item_code')
    item_type = request.args.get('item_type', '')  # Expected: 'FG', 'WIPF', or 'WIP'
    
    if not item_code:
        return jsonify({'valid': False, 'message': 'Item code required'})
    
    # Use proper relationship query to filter by item type
    query = ItemMaster.query.filter_by(item_code=item_code)
    if item_type:
        query = query.join(ItemMaster.item_type).filter(ItemMaster.item_type.has(type_name=item_type))
    
    item = query.first()
    if item:
        return jsonify({
            'valid': True,
            'description': item.description,
            'item_type': item.item_type.type_name if item.item_type else 'Unknown'
        })
    else:
        return jsonify({'valid': False, 'message': f'Item not found{" of type " + item_type if item_type else ""}'})

@joining_bp.route('/api/joining/items/<item_type>')
def get_items_by_type(item_type):
    """API endpoint to get items by type for auto-suggestions"""
    query = request.args.get('q', '')
    
    # Use proper relationship query to filter by item type
    items_query = ItemMaster.query.join(ItemMaster.item_type).filter(
        ItemMaster.item_type.has(type_name=item_type)
    )
    
    if query:
        items_query = items_query.filter(
            or_(
                ItemMaster.item_code.contains(query),
                ItemMaster.description.contains(query)
            )
        )
    
    items = items_query.limit(10).all()
    
    return jsonify([{
        'item_code': item.item_code,
        'description': item.description,
        'item_type': item.item_type.type_name if item.item_type else 'Unknown'
    } for item in items]) 