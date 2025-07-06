import pandas as pd
import os
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from sqlalchemy.sql import text
from sqlalchemy import asc, desc
from werkzeug.utils import secure_filename
from datetime import datetime, date
import pytz
import math

from controllers.packing_controller import update_packing_entry
from controllers.enhanced_bom_service import EnhancedBOMService
from models.item_master import ItemMaster
from models.packing import Packing
from models.filling import Filling
from models.production import Production
# from models.joining import Joining  # REMOVED - using item_master hierarchy


soh_bp = Blueprint('soh', __name__, template_folder='templates')

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_packing_entry_from_soh(fg_code, description, week_commencing, soh_total_units, item):
    """
    Create or update a packing entry when SOH data is uploaded.
    This is a simplified version specifically for SOH uploads.
    Now uses the enhanced BOM service with joining table for optimized performance.
    """
    from app import db
    from models.packing import Packing
    from models.filling import Filling
    from models.production import Production
    
    try:
        # Get all required values from ItemMaster
        avg_weight_per_unit = item.kg_per_unit or item.avg_weight_per_unit or 0.0
        min_level = item.min_level or 0.0
        max_level = item.max_level or 0.0
        calculation_factor = item.calculation_factor or 0.0
        
        print(f"Processing SOH->Packing for {fg_code}: soh_units={soh_total_units}, avg_weight={avg_weight_per_unit}, calc_factor={calculation_factor}")
        
        # Calculate SOH requirement based on min/max levels
        soh_requirement_units_week = int(max_level - soh_total_units) if soh_total_units < min_level else 0
        
        # Check if packing entry already exists
        existing_packing = Packing.query.filter_by(
            item_id=item.id,
            week_commencing=week_commencing,
            packing_date=week_commencing  # Use week_commencing as packing_date for SOH-generated entries
        ).first()
        
        if existing_packing:
            packing = existing_packing
            packing.soh_requirement_units_week = soh_requirement_units_week
            packing.soh_units = soh_total_units
            packing.avg_weight_per_unit = avg_weight_per_unit
            packing.calculation_factor = calculation_factor
        else:
            packing = Packing(
                packing_date=week_commencing,
                item_id=item.id,
                week_commencing=week_commencing,
                soh_requirement_units_week=soh_requirement_units_week,
                soh_units=soh_total_units,
                avg_weight_per_unit=avg_weight_per_unit,
                calculation_factor=calculation_factor
            )
            db.session.add(packing)
        
        # Calculate derived values
        packing.soh_kg = round(soh_total_units * avg_weight_per_unit, 0) if avg_weight_per_unit else 0
        packing.soh_requirement_kg_week = int(soh_requirement_units_week * avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.total_stock_kg = packing.soh_requirement_kg_week * calculation_factor if calculation_factor is not None else 0
        packing.total_stock_units = math.ceil(packing.total_stock_kg / avg_weight_per_unit) if avg_weight_per_unit else 0
        packing.requirement_kg = round(packing.total_stock_kg - packing.soh_kg + (packing.special_order_kg or 0), 0) if (packing.total_stock_kg - packing.soh_kg + (packing.special_order_kg or 0)) > 0 else 0
        packing.requirement_unit = packing.total_stock_units - soh_total_units + (packing.special_order_unit or 0) if (packing.total_stock_units - soh_total_units + (packing.special_order_unit or 0)) > 0 else 0
        
        db.session.commit()
        print(f"✓ Packing entry saved: requirement_kg={packing.requirement_kg}, requirement_unit={packing.requirement_unit}")
        
        # Use Enhanced BOM Service for downstream requirements creation
        if packing.requirement_kg > 0:
            try:
                # Calculate downstream requirements using joining table
                requirements = EnhancedBOMService.calculate_downstream_requirements(
                    fg_code, packing.requirement_kg
                )
                
                if requirements:
                    created_entries = []
                    
                    # Create filling entry if needed
                    if 'filling' in requirements:
                        filling_req = requirements['filling']
                        # Find the item by item_code to get its ID
                        filling_item = ItemMaster.query.filter_by(item_code=filling_req['item_code']).first()
                        if filling_item:
                            existing_filling = Filling.query.filter_by(
                                item_id=filling_item.id,
                                week_commencing=week_commencing
                            ).first()
                            
                            if not existing_filling:
                                filling = Filling(
                                    item_id=filling_item.id,
                                    filling_date=week_commencing,  # Use filling_date field
                                    week_commencing=week_commencing,
                                    kilo_per_size=filling_req['requirement_kg']  # Add the requirement_kg value
                                )
                                db.session.add(filling)
                                created_entries.append(f"Filling: {filling_req['item_code']}")
                    
                    # Create production entry if needed
                    if 'production' in requirements:
                        production_req = requirements['production']
                        # Find the item by item_code to get its ID
                        production_item = ItemMaster.query.filter_by(item_code=production_req['item_code']).first()
                        if production_item:
                            existing_production = Production.query.filter_by(
                                item_id=production_item.id,
                                week_commencing=week_commencing
                            ).first()
                            
                            if not existing_production:
                                # Calculate batches (using 100kg as default batch size, or item-specific if available)
                                batches = production_req['requirement_kg'] / 100.0 if production_req['requirement_kg'] > 0 else 0.0
                                
                                production = Production(
                                    item_id=production_item.id,
                                    production_date=week_commencing,  # Use production_date field
                                    production_code=production_req['item_code'],  # Keep for compatibility
                                    week_commencing=week_commencing,
                                    total_kg=production_req['requirement_kg'],  # Use total_kg field
                                    batches=batches  # Add batches calculation
                                )
                                db.session.add(production)
                                created_entries.append(f"Production: {production_req['item_code']}")
                    
                    # Commit downstream entries
                    db.session.commit()
                    
                    if created_entries:
                        message = f"Packing created. Downstream entries: {', '.join(created_entries)}"
                        print(f"✓ Enhanced BOM successful: {message}")
                        return True, message
                    else:
                        print("✓ Enhanced BOM: No new downstream entries needed")
                        return True, "Packing created (existing downstream entries found)"
                        
                else:
                    # No hierarchy found, fall back to direct production
                    print(f"✓ No hierarchy found for {fg_code}, direct production flow")
                    return True, "Packing created (direct production flow)"
                    
            except Exception as e:
                print(f"✗ Enhanced BOM failed: {str(e)}")
                # Don't fail the whole operation, packing was still created
                return True, f"Packing created but enhanced BOM failed: {str(e)}"
        else:
            print("✓ Packing entry created (no downstream requirements due to zero kg)")
            return True, "Packing entry created"
            
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error creating packing entry: {str(e)}")
        return False, str(e)

@soh_bp.route('/soh_upload', methods=['GET', 'POST'])
def soh_upload():
    from app import db
    from models.soh import SOH
    from models.item_master import ItemMaster

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file uploaded!", "danger")
            return render_template('soh/upload.html', current_page="soh")

        file = request.files['file']
        sheet_name = request.form.get('sheet_name', '').strip() or 'SOH'
        form_week_commencing = request.form.get('week_commencing', '').strip()

        if file.filename == '':
            flash("No file selected!", "danger")
            return render_template('soh/upload.html', current_page="soh")

        if not file or not allowed_file(file.filename):
            flash("Invalid file type! Only CSV, XLSX, or XLS files are allowed.", "danger")
            return render_template('soh/upload.html', current_page="soh")

        temp_path = None
        try:
            filename = secure_filename(file.filename)
            temp_path = os.path.join('uploads', filename)
            os.makedirs('uploads', exist_ok=True)
            file.save(temp_path)

            if filename.endswith('.csv'):
                df = pd.read_csv(temp_path)
            else:
                with pd.ExcelFile(temp_path) as excel_file:
                    if sheet_name not in excel_file.sheet_names:
                        flash(f"Sheet '{sheet_name}' not found in the Excel file. Available sheets: {', '.join(excel_file.sheet_names)}", "danger")
                        return render_template('soh/upload.html', current_page="soh")
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)

            df.columns = df.columns.str.strip()

            required_columns = ['Week Commencing', 'FG Code', 'Description', 'Soh_dispatch_Box', 'Soh_dispatch_Unit', 'Soh_packing_Box', 'Soh_packing_Unit', 'Soh_total_Box', 'Soh_total_Unit']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f"Missing required columns in file! Missing: {', '.join(missing_columns)}. Expected: {', '.join(required_columns)}", "danger")
                return render_template('soh/upload.html', current_page="soh")

            numeric_columns = ['Soh_dispatch_Box', 'Soh_dispatch_Unit', 'Soh_packing_Box', 'Soh_packing_Unit', 'Soh_total_Box', 'Soh_total_Unit']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

            # Parse form week_commencing if provided
            form_week_commencing_date = None
            if form_week_commencing:
                try:
                    # Expect YYYY-MM-DD from form input type="date"
                    form_week_commencing_date = datetime.strptime(form_week_commencing, '%Y-%m-%d').date()
                except ValueError:
                    flash(f"Invalid Week Commencing date format in form: {form_week_commencing}. Expected format: YYYY-MM-DD.", "danger")
                    return render_template('soh/upload.html', current_page="soh")

            # Counters for tracking created entries
            soh_processed = 0
            packing_created = 0
            packing_failed = 0

            for _, row in df.iterrows():
                print("Processing row:", row.to_dict())

                fg_code = str(row['FG Code']).strip()
                description = str(row['Description']).strip() if pd.notnull(row['Description']) else ''

                def safe_float(value):
                    try:
                        if pd.notnull(value) and value != '':
                            return float(value)
                        return 0.0
                    except (ValueError, TypeError) as e: # Catch the exception 'e' here
                        print(f"Error converting value '{value}' to float: {e}")
                        return 0.0

                dispatch_boxes = safe_float(row['Soh_dispatch_Box'])
                dispatch_units = safe_float(row['Soh_dispatch_Unit'])
                packing_boxes = safe_float(row['Soh_packing_Box'])
                packing_units = safe_float(row['Soh_packing_Unit'])
                # soh_total_boxes and soh_total_units will be recalculated, so no need to parse from file directly

                # Use form_week_commencing if provided, else parse from file
                week_commencing = form_week_commencing_date
                if not week_commencing and pd.notnull(row['Week Commencing']):
                    try:
                        week_commencing_val = row['Week Commencing']
                        if isinstance(week_commencing_val, pd.Timestamp):
                            week_commencing = week_commencing_val.date()
                        else:
                            week_commencing_str = str(week_commencing_val).strip()
                            # try multiple date formats
                            for fmt in ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']:
                                try:
                                    week_commencing = datetime.strptime(week_commencing_str, fmt).date()
                                    break
                                except ValueError:
                                    continue
                            else:
                                flash(f"Invalid Week Commencing date format in file: {week_commencing_str}. Expected formats: DD-MM-YYYY, YYYY-MM-DD, DD/MM/YYYY, or YYYY/MM/DD. Skipping row for FG Code: {fg_code}", "danger")
                                continue # Skip this row and continue with the next

                    except (ValueError, TypeError) as e:
                        flash(f"Error converting Week Commencing '{row['Week Commencing']}' to date for FG Code {fg_code}: {str(e)}", "danger")
                        continue # Skip this row and continue with the next

                if not week_commencing:
                    flash(f"Week Commencing date is missing or invalid for FG Code: {fg_code}. Skipping row.", "danger")
                    continue

                item = ItemMaster.query.filter_by(item_code=fg_code).first()
                if not item:
                    flash(f"No item found for FG Code: {fg_code}. Skipping row.", "danger")
                    continue
                units_per_bag = item.units_per_bag if item and item.units_per_bag else 1
                avg_weight_per_unit = item.kg_per_unit if item and item.kg_per_unit else 0.0


                # Recalculate totals to ensure consistency (ALWAYS recalculate on the backend)
                soh_total_boxes_calc = dispatch_boxes + packing_boxes
                soh_total_units_calc = (
                    (dispatch_boxes * units_per_bag) +
                    (packing_boxes * units_per_bag) +
                    dispatch_units +
                    packing_units
                )

                with db.session.no_autoflush:
                    # Use foreign key relationship instead of fg_code
                    soh = SOH.query.filter_by(item_id=item.id, week_commencing=week_commencing).first()
                    if soh:
                        # Check for Packing entries that reference the current SOH
                        # Use the item's foreign key relationship
                        packing_entries = Packing.query.filter_by(week_commencing=soh.week_commencing, item_id=item.id).all()
                        if packing_entries and soh.week_commencing != week_commencing: # Only update if week_commencing changed
                            for packing in packing_entries:
                                packing.week_commencing = week_commencing
                            # Don't commit here, commit after SOH update
                        # db.session.commit() # Removed this commit here, it was causing issues.

                        soh.description = description
                        soh.soh_dispatch_boxes = dispatch_boxes
                        soh.soh_dispatch_units = dispatch_units
                        soh.soh_packing_boxes = packing_boxes
                        soh.soh_packing_units = packing_units
                        soh.soh_total_boxes = soh_total_boxes_calc # Use calculated values
                        soh.soh_total_units = soh_total_units_calc # Use calculated values
                        soh.edit_date = datetime.now(pytz.timezone('Australia/Sydney'))
                        print(f"Updating SOH for {fg_code}: {soh.__dict__}")
                    else:
                        new_soh = SOH(
                            week_commencing=week_commencing,
                            item_id=item.id,  # Use foreign key
                            fg_code=fg_code,  # Keep for backward compatibility
                            description=description,
                            soh_dispatch_boxes=dispatch_boxes,
                            soh_dispatch_units=dispatch_units,
                            soh_packing_boxes=packing_boxes,
                            soh_packing_units=packing_units,
                            soh_total_boxes=soh_total_boxes_calc, # Use calculated values
                            soh_total_units=soh_total_units_calc, # Use calculated values
                            edit_date=datetime.now(pytz.timezone('Australia/Sydney'))
                        )
                        db.session.add(new_soh)
                        print(f"Creating new SOH for {fg_code}: {new_soh.__dict__}")

                    # Commit SOH entry before updating Packing (or at the end of the loop)
                    # It's better to commit once outside the loop for performance,
                    # but if you need `soh.id` immediately for subsequent updates within the loop,
                    # then an individual commit here might be necessary, or a flush.
                    # For now, let's keep it here for data consistency before related updates.
                    db.session.commit() # Commit changes to SOH and Packing entries if any
                    soh_processed += 1

                    # Automatically create Packing (and related Filling/Production) entries
                    if soh_total_boxes_calc >= 0 or soh_total_units_calc >= 0:
                        success, message = create_packing_entry_from_soh(
                            fg_code=fg_code,
                            description=description,
                            week_commencing=week_commencing,
                            soh_total_units=soh_total_units_calc,
                            item=item
                        )
                        if success:
                            packing_created += 1
                            print(f"✓ Auto-created entries for {fg_code}: {message}")
                        else:
                            packing_failed += 1
                            flash(f"Warning: Could not create entries for FG Code {fg_code}: {message}", "warning")

            # Provide detailed summary to user
            flash(f"SOH data uploaded successfully! Processed {soh_processed} SOH entries.", "success")
            if packing_created > 0:
                flash(f"✓ Automatically created {packing_created} packing entries (with related filling/production entries where applicable).", "success")
            if packing_failed > 0:
                flash(f"⚠ Failed to create packing entries for {packing_failed} products. Check warnings above.", "warning")
            return redirect(url_for('soh.soh_list'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error processing file: {str(e)}", "danger")
            return render_template('soh/upload.html', current_page="soh")

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except PermissionError as e:
                    print(f"Warning: Could not delete temporary file {temp_path}: {e}")

    return render_template('soh/upload.html', current_page="soh")

@soh_bp.route('/soh_list', methods=['GET'])
def soh_list():
    from app import db
    from models.soh import SOH

    search_fg_code = request.args.get('fg_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip() # This will be YYYY-MM-DD from frontend
    sort_by = request.args.get('sort_by', 'id').strip()
    sort_direction = request.args.get('sort_direction', 'asc').strip()

    sohs = [] # Initialize sohs as an empty list
    try:
        sohs_query = SOH.query.join(ItemMaster, SOH.item_id == ItemMaster.id)
        if search_fg_code:
            sohs_query = sohs_query.filter(ItemMaster.item_code.ilike(f"%{search_fg_code}%"))
        if search_description:
            sohs_query = sohs_query.filter(SOH.description.ilike(f"%{search_description}%"))
        if search_week_commencing:
            try:
                # Parse YYYY-MM-DD from the frontend search input
                week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
                sohs_query = sohs_query.filter(SOH.week_commencing == week_commencing_date)
            except ValueError as e:
                flash(f"Invalid Week Commencing date format in search: {str(e)}. Please use YYYY-MM-DD.", "danger")
                return render_template('soh/list.html',
                                       sohs=[], # Pass an empty list on error
                                       search_fg_code=search_fg_code,
                                       search_description=search_description,
                                       search_week_commencing=search_week_commencing,
                                       sort_by=sort_by,
                                       sort_direction=sort_direction,
                                       current_page="soh")

        # Apply sorting
        if sort_by in ['week_commencing', 'fg_code', 'description', 'edit_date']:
            if sort_direction == 'desc':
                sohs_query = sohs_query.order_by(desc(getattr(SOH, sort_by)))
            else:
                sohs_query = sohs_query.order_by(asc(getattr(SOH, sort_by)))

        sohs = sohs_query.all()

        for soh in sohs:
            # Format dates for display in DD-MM-YYYY format for the initial render
            soh.week_commencing_str = soh.week_commencing.strftime('%d-%m-%Y') if soh.week_commencing else ''
            soh.edit_date_str = soh.edit_date.strftime('%d-%m-%Y %H:%M:%S') if soh.edit_date else ''

    except Exception as e:
        flash(f"Error fetching SOH list: {str(e)}", "danger")
        sohs = [] # Ensure it's an empty list if an exception occurs

    return render_template('soh/list.html',
                           sohs=sohs,
                           search_fg_code=search_fg_code,
                           search_description=search_description,
                           search_week_commencing=search_week_commencing, # Pass YYYY-MM-DD back to keep form value
                           sort_by=sort_by,
                           sort_direction=sort_direction,
                           current_page="soh")

@soh_bp.route('/soh_create', methods=['GET', 'POST'])
def soh_create():
    from app import db
    from models.soh import SOH
    from models.item_master import ItemMaster

    if request.method == 'POST':
        try:
            fg_code = request.form['fg_code'].strip()
            week_commencing = request.form.get('week_commencing')
            description = request.form['description'].strip()
            # Convert empty strings from form to 0.0 or None as needed
            dispatch_boxes = float(request.form.get('soh_dispatch_boxes') or 0.0)
            dispatch_units = float(request.form.get('soh_dispatch_units') or 0.0)
            packing_boxes = float(request.form.get('soh_packing_boxes') or 0.0)
            packing_units = float(request.form.get('soh_packing_units') or 0.0)

            # Convert week_commencing to date (expected YYYY-MM-DD from HTML date input)
            week_commencing_date = None
            if week_commencing:
                try:
                    week_commencing_date = datetime.strptime(week_commencing, '%Y-%m-%d').date()
                except ValueError as e:
                    flash(f"Invalid Week Commencing date format: {str(e)}. Expected YYYY-MM-DD.", "danger")
                    return redirect(request.url)

            item = ItemMaster.query.filter_by(item_code=fg_code).first()
            if not item:
                return jsonify({"success": False, "error": f"No item found for FG Code: {fg_code}"}), 400
            units_per_bag = item.units_per_bag if item and item.units_per_bag else 1
            avg_weight_per_unit = item.kg_per_unit if item and item.kg_per_unit else 0.0

            soh_total_boxes = dispatch_boxes + packing_boxes
            soh_total_units = (
                (dispatch_boxes * units_per_bag) +
                (packing_boxes * units_per_bag) +
                dispatch_units +
                packing_units
            )

            new_soh = SOH(
                item_id=item.id,  # Use foreign key
                fg_code=fg_code,  # Keep for backward compatibility
                week_commencing=week_commencing_date,
                description=description,
                soh_dispatch_boxes=dispatch_boxes,
                soh_dispatch_units=dispatch_units,
                soh_packing_boxes=packing_boxes,
                soh_packing_units=packing_units,
                soh_total_boxes=soh_total_boxes,
                soh_total_units=soh_total_units,
                edit_date=datetime.now(pytz.timezone('Australia/Sydney'))
            )
            db.session.add(new_soh)
            db.session.commit()

            if soh_total_boxes >= 0 or soh_total_units >= 0: # Condition for update_packing_entry
                # Ensure packing_date is a date object
                packing_date_for_update = week_commencing_date if week_commencing_date else date.today()
                success, message = create_packing_entry_from_soh(
                    fg_code=fg_code,
                    description=description,
                    week_commencing=packing_date_for_update,
                    soh_total_units=soh_total_units,
                    item=item
                )
                if not success:
                    flash(f"Warning: Could not update Packing for FG Code {fg_code}: {message}", "warning")

            flash("SOH entry created successfully!", "success")
            return redirect(url_for('soh.soh_list'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating SOH entry: {str(e)}", "danger")
            return redirect(request.url)

    fg_code = request.args.get('fg_code', '')
    return render_template('soh/create.html', fg_code=fg_code, current_page="soh")

@soh_bp.route('/soh_edit/<int:id>', methods=['GET', 'POST'])
def soh_edit(id):
    from app import db
    from models.soh import SOH
    from models.item_master import ItemMaster

    soh = SOH.query.get_or_404(id)

    if request.method == 'POST':
        try:
            fg_code = request.form['fg_code'].strip()
            week_commencing = request.form.get('week_commencing')
            description = request.form['description'].strip()
            soh_dispatch_boxes = float(request.form.get('soh_dispatch_boxes') or 0.0)
            soh_dispatch_units = float(request.form.get('soh_dispatch_units') or 0.0)
            soh_packing_boxes = float(request.form.get('soh_packing_boxes') or 0.0)
            soh_packing_units = float(request.form.get('soh_packing_units') or 0.0)

            # Convert week_commencing to date (expected YYYY-MM-DD from HTML date input)
            week_commencing_date = None
            if week_commencing:
                try:
                    week_commencing_date = datetime.strptime(week_commencing, '%Y-%m-%d').date()
                except ValueError:
                    # Fallback for DD-MM-YYYY, although YYYY-MM-DD is expected from input type="date"
                    try:
                        week_commencing_date = datetime.strptime(week_commencing, '%d-%m-%Y').date()
                    except ValueError as e:
                        flash(f"Invalid Week Commencing date format: {str(e)}. Please use YYYY-MM-DD.", "danger")
                        return redirect(request.url)

            item = ItemMaster.query.filter_by(item_code=fg_code).first()
            if not item:
                flash(f"FG Code '{fg_code}' not found in Item Master table.", "danger")
                return redirect(request.url)
            units_per_bag = item.units_per_bag if item and item.units_per_bag else 1
            avg_weight_per_unit = item.kg_per_unit if item and item.kg_per_unit else 0.0

            # Recalculate totals
            soh_total_boxes = soh_dispatch_boxes + soh_packing_boxes
            soh_total_units = (
                (soh_dispatch_boxes * units_per_bag) +
                (soh_packing_boxes * units_per_bag) +
                soh_dispatch_units +
                soh_packing_units
            )

            # Update item_id if fg_code changed
            if fg_code != (soh.item.item_code if soh.item else soh.fg_code):
                new_item = ItemMaster.query.filter_by(item_code=fg_code).first()
                if new_item:
                    soh.item_id = new_item.id
                else:
                    flash(f"No item found for FG Code: {fg_code}", "danger")
                    return redirect(request.url)
            soh.fg_code = fg_code  # Keep for backward compatibility
            soh.week_commencing = week_commencing_date
            soh.description = description
            soh.soh_dispatch_boxes = soh_dispatch_boxes
            soh.soh_dispatch_units = soh_dispatch_units
            soh.soh_packing_boxes = soh_packing_boxes
            soh.soh_packing_units = soh_packing_units
            soh.soh_total_boxes = soh_total_boxes # Use calculated values
            soh.soh_total_units = soh_total_units # Use calculated values
            soh.edit_date = datetime.now(pytz.timezone('Australia/Sydney'))

            db.session.commit()

            if soh_total_boxes > 0 or soh_total_units > 0: # Condition for update_packing_entry
                # Fetch item to get calculation_factor
                item = ItemMaster.query.filter_by(item_code=fg_code).first()
                avg_weight_per_unit = item.kg_per_unit if item and item.kg_per_unit else 0.0
                
                packing_date = week_commencing_date if week_commencing_date else date.today()
                success, message = create_packing_entry_from_soh(
                    fg_code=fg_code,
                    description=description,
                    week_commencing=packing_date,
                    soh_total_units=soh_total_units,
                    item=item
                )
                if not success:
                    flash(f"Warning: Could not update Packing for FG Code {fg_code}: {message}", "warning")

            flash("SOH entry updated successfully!", "success")
            return redirect(url_for('soh.soh_list'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating SOH entry: {str(e)}", "danger")
            return redirect(request.url)

    # Format edit_date and week_commencing for display in the form (YYYY-MM-DD for input type="date")
    soh.edit_date_str = soh.edit_date.strftime('%d-%m-%Y %H:%M:%S') if soh.edit_date else ''
    soh.week_commencing_str = soh.week_commencing.strftime('%Y-%m-%d') if soh.week_commencing else '' # For <input type="date">

    return render_template('soh/edit.html', soh=soh, current_page="soh")


@soh_bp.route('/soh_delete/<int:id>', methods=['POST'])
def soh_delete(id):
    from app import db
    from models.soh import SOH
    # from datetime import datetime # Already imported

    try:
        soh = SOH.query.get_or_404(id)
        db.session.delete(soh)
        db.session.commit()
        flash("SOH entry deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting SOH entry: {str(e)}", "danger")

    return redirect(url_for('soh.soh_list'))

@soh_bp.route('/autocomplete_soh', methods=['GET'])
def autocomplete_soh():
    from app import db
    from models.item_master import ItemMaster

    search = request.args.get('query', '').strip()

    if not search:
        return jsonify([])

    try:
        # Use SQLAlchemy's ORM for better integration and less raw SQL
        results = db.session.query(ItemMaster.item_code, ItemMaster.description).join(
            ItemMaster.item_type
        ).filter(
            ItemMaster.item_code.ilike(f"{search}%"),
            ItemMaster.item_type.has(type_name='FG') | ItemMaster.item_type.has(type_name='WIPF')
        ).limit(10).all()
        suggestions = [{"fg_code": row.item_code, "description": row.description} for row in results]
        return jsonify(suggestions)
    except Exception as e:
        print("Error fetching SOH autocomplete suggestions:", e)
        return jsonify([])


@soh_bp.route('/get_search_sohs', methods=['GET'])
def get_search_sohs():
    from app import db
    from models.soh import SOH
    from datetime import datetime

    search_fg_code = request.args.get('fg_code', '').strip()
    search_description = request.args.get('description', '').strip()
    search_week_commencing = request.args.get('week_commencing', '').strip()
    sort_by = request.args.get('sort_by', 'id').strip()
    sort_direction = request.args.get('sort_direction', 'asc').strip()

    try:
        sohs_query = SOH.query.join(ItemMaster, SOH.item_id == ItemMaster.id)

        if search_fg_code:
            sohs_query = sohs_query.filter(ItemMaster.item_code.ilike(f"%{search_fg_code}%"))
        if search_description:
            sohs_query = sohs_query.filter(SOH.description.ilike(f"%{search_description}%"))
        if search_week_commencing:
            try:
                # Expect YYYY-MM-DD from frontend search input
                week_commencing_date = datetime.strptime(search_week_commencing, '%Y-%m-%d').date()
                sohs_query = sohs_query.filter((SOH.week_commencing == week_commencing_date))
            except ValueError:
                # If date is invalid, return empty result instead of error
                return jsonify([])

        # Apply sorting
        if sort_by in ['week_commencing', 'fg_code', 'description', 'edit_date']:
            if sort_direction == 'desc':
                sohs_query = sohs_query.order_by(desc(getattr(SOH, sort_by)))
            else:
                sohs_query = sohs_query.order_by(asc(getattr(SOH, sort_by)))

        sohs = sohs_query.all()
        # print(f"Filtered SOH count: {len(sohs)}") # Debugging line

        sohs_data = []
        for soh in sohs:
            # For inline editing `data-original-input` attribute, `week_commencing` needs to be YYYY-MM-DD
            # for the HTML input type="date" to populate correctly.
            # The display in the table cell itself should be DD-MM-YYYY.
            week_commencing_display = soh.week_commencing.strftime('%d-%m-%Y') if soh.week_commencing else ""
            week_commencing_input = soh.week_commencing.strftime('%Y-%m-%d') if soh.week_commencing else ""

            sohs_data.append({
                "id": soh.id,
                "week_commencing": week_commencing_display, # For displaying in the table (DD-MM-YYYY)
                "week_commencing_original": week_commencing_input, # For data-original-input attribute (YYYY-MM-DD)
                "fg_code": soh.item.item_code if soh.item else (soh.fg_code or ""),  # Use foreign key relationship
                "description": soh.description or "",
                "soh_dispatch_boxes": soh.soh_dispatch_boxes if soh.soh_dispatch_boxes is not None else "",
                "soh_dispatch_units": soh.soh_dispatch_units if soh.soh_dispatch_units is not None else "",
                "soh_packing_boxes": soh.soh_packing_boxes if soh.soh_packing_boxes is not None else "",
                "soh_packing_units": soh.soh_packing_units if soh.soh_packing_units is not None else "",
                "soh_total_boxes": soh.soh_total_boxes if soh.soh_total_boxes is not None else "",
                "soh_total_units": soh.soh_total_units if soh.soh_total_units is not None else "",
                "edit_date": soh.edit_date.strftime('%d-%m-%Y %H:%M:%S') if soh.edit_date else ""
            })

        return jsonify(sohs_data)
    except Exception as e:
        print(f"Error fetching search SOHs: {str(e)}")
        return jsonify([]), 500

@soh_bp.route('/soh_bulk_edit', methods=['POST'])
def soh_bulk_edit():
    from app import db
    from models.soh import SOH
    from models.item_master import ItemMaster
    # from datetime import datetime # Already imported

    try:
        data = request.get_json()
        ids = data.get('ids', [])
        if not ids:
            return jsonify({"success": False, "error": "No SOH entries selected"}), 400

        week_commencing_str = data.get('week_commencing', '').strip()
        soh_dispatch_boxes_str = data.get('soh_dispatch_boxes', '')
        soh_dispatch_units_str = data.get('soh_dispatch_units', '')
        soh_packing_boxes_str = data.get('soh_packing_boxes', '')
        soh_packing_units_str = data.get('soh_packing_units', '')

        # Convert and validate inputs
        week_commencing_date = None
        if week_commencing_str:
            try:
                week_commencing_date = datetime.strptime(week_commencing_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"success": False, "error": "Invalid Week Commencing date format. Use YYYY-MM-DD"}), 400

        # Convert numeric fields, allowing empty strings to skip updates (set to None)
        def parse_float_or_none(value_str):
            try:
                return float(value_str) if value_str.strip() != '' else None
            except (ValueError, TypeError):
                return None # Return None if conversion fails

        dispatch_boxes_input = parse_float_or_none(soh_dispatch_boxes_str)
        dispatch_units_input = parse_float_or_none(soh_dispatch_units_str)
        packing_boxes_input = parse_float_or_none(soh_packing_boxes_str)
        packing_units_input = parse_float_or_none(soh_packing_units_str)


        for soh_id in ids:
            soh = SOH.query.get(soh_id) # Use .get() as get_or_404 would raise an error and break the loop
            if not soh:
                print(f"SOH entry with ID {soh_id} not found, skipping.")
                continue # Skip to the next ID if not found

            # Update only fields that were provided (not None)
            if week_commencing_date is not None:
                soh.week_commencing = week_commencing_date
            if dispatch_boxes_input is not None:
                soh.soh_dispatch_boxes = dispatch_boxes_input
            if dispatch_units_input is not None:
                soh.soh_dispatch_units = dispatch_units_input
            if packing_boxes_input is not None:
                soh.soh_packing_boxes = packing_boxes_input
            if packing_units_input is not None:
                soh.soh_packing_units = packing_units_input

            # Use the foreign key relationship if available, fallback to fg_code
            item = soh.item if soh.item else ItemMaster.query.filter_by(item_code=soh.fg_code).first()
            if not item:
                fg_code = soh.item.item_code if soh.item else soh.fg_code
                return jsonify({"success": False, "error": f"No item found for FG Code: {fg_code}"}), 400
            units_per_bag = item.units_per_bag if item and item.units_per_bag else 1
            avg_weight_per_unit = item.kg_per_unit if item and item.kg_per_unit else 0.0


            # Recalculate totals based on potentially updated or existing values
            # Ensure these use actual float/numeric values, not None
            current_dispatch_boxes = soh.soh_dispatch_boxes or 0.0
            current_dispatch_units = soh.soh_dispatch_units or 0.0
            current_packing_boxes = soh.soh_packing_boxes or 0.0
            current_packing_units = soh.soh_packing_units or 0.0

            soh.soh_total_boxes = current_dispatch_boxes + current_packing_boxes
            soh.soh_total_units = (
                (current_dispatch_boxes * units_per_bag) +
                (current_packing_boxes * units_per_bag) +
                current_dispatch_units +
                current_packing_units
            )

            soh.edit_date = datetime.now(pytz.timezone('Australia/Sydney'))

            # Update packing entry if necessary
            # Pass the current soh.week_commencing (which might have just been updated)
            if soh.soh_total_boxes >= 0 or soh.soh_total_units >= 0: # Condition for create_packing_entry_from_soh
                packing_date_for_update = soh.week_commencing if soh.week_commencing else date.today()
                fg_code = soh.item.item_code if soh.item else soh.fg_code
                success, message = create_packing_entry_from_soh(
                    fg_code=fg_code,
                    description=soh.description,
                    week_commencing=packing_date_for_update,
                    soh_total_units=soh.soh_total_units or 0,
                    item=item
                )
                if not success:
                    print(f"Failed to update Packing for {soh.fg_code} during bulk edit: {message}")

        db.session.commit()
        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        print(f"Error in bulk edit: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@soh_bp.route('/soh_inline_edit', methods=['POST'])
def soh_inline_edit():
    from app import db
    from models.soh import SOH
    from models.item_master import ItemMaster
    # from datetime import datetime, date # Already imported

    try:
        data = request.get_json()
        print(f"Received data for inline edit: {data}")
        soh_id = data.get('id')
        if not soh_id:
            return jsonify({"success": False, "error": "No SOH ID provided"}), 400

        soh = SOH.query.get_or_404(soh_id)
        field = data.get('field')
        value = data.get(field) # This value is what the frontend sent for the specific field

        if not field:
            return jsonify({"success": False, "error": "No field provided"}), 400

        print(f"Processing field: {field}, value: '{value}'")

        if field == 'week_commencing':
            try:
                if value:
                    # Frontend sends YYYY-MM-DD from the date input
                    parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
                else:
                    parsed_date = None # Allow setting to null/empty
                soh.week_commencing = parsed_date
            except ValueError as e:
                print(f"Date parsing error: {str(e)}")
                return jsonify({"success": False, "error": f"Invalid date format: {str(e)}. Use YYYY-MM-DD."}), 400
        elif field in ['soh_dispatch_boxes', 'soh_dispatch_units', 'soh_packing_boxes', 'soh_packing_units']:
            try:
                # Convert empty string from frontend to 0.0 or None as per database column allows nulls or defaults
                # Assuming these should be 0.0 if empty for calculations.
                numeric_value = float(value) if value is not None and value != '' else 0.0
                setattr(soh, field, numeric_value)
            except (ValueError, TypeError) as e:
                print(f"Number conversion error for {field}: {str(e)}")
                return jsonify({"success": False, "error": f"Invalid number for {field}: {str(e)}."}), 400
        else:
            return jsonify({"success": False, "error": f"Invalid field specified: {field}."}), 400

        # Retrieve current item for calculating totals and updating packing
        item = soh.item if soh.item else ItemMaster.query.filter_by(item_code=soh.fg_code).first()
        if not item:
            fg_code = soh.item.item_code if soh.item else soh.fg_code
            return jsonify({"success": False, "error": f"No item found for FG Code: {fg_code}"}), 400
        units_per_bag = item.units_per_bag if item and item.units_per_bag else 1
        avg_weight_per_unit = item.kg_per_unit if item and item.kg_per_unit else 0.0

        # Recalculate total boxes and units based on potentially updated and existing values
        # Ensure these are treated as 0.0 if they are None for calculation purposes
        current_dispatch_boxes = soh.soh_dispatch_boxes or 0.0
        current_dispatch_units = soh.soh_dispatch_units or 0.0
        current_packing_boxes = soh.soh_packing_boxes or 0.0
        current_packing_units = soh.soh_packing_units or 0.0

        soh.soh_total_boxes = current_dispatch_boxes + current_packing_boxes
        soh.soh_total_units = (
            (current_dispatch_boxes * units_per_bag) +
            (current_packing_boxes * units_per_bag) +
            current_dispatch_units +
            current_packing_units
        )

        soh.edit_date = datetime.now(pytz.timezone('Australia/Sydney'))

        # Update packing entry if necessary
        if soh.soh_total_boxes >= 0 or soh.soh_total_units >= 0:
            # Ensure packing_date is a date object for create_packing_entry_from_soh
            packing_date = soh.week_commencing if soh.week_commencing else date.today()
            success, message = create_packing_entry_from_soh(
                fg_code=soh.fg_code,
                description=soh.description,
                week_commencing=packing_date,
                soh_total_units=soh.soh_total_units or 0,
                item=item
            )
            if not success:
                print(f"Failed to update Packing for {soh.fg_code} during inline edit: {message}")
                # Consider if you want to flash a warning for inline edits too
                # flash(message, "warning")

        db.session.commit()
        print(f"SOH updated successfully: {soh.id}")
        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        print(f"Error in inline edit: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500