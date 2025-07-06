from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from models.item_master import ItemMaster
from models.inventory import Inventory
from models.category import Category
from models.production import Production
from database import db
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

inventory_bp = Blueprint('inventory', __name__, template_folder='../templates')

def get_rm_type_id():
    """Helper function to get RM item type ID"""
    from models.item_type import ItemType
    rm_type = ItemType.query.filter_by(type_name='RM').first()
    return rm_type.id if rm_type else None

@inventory_bp.route('/inventory')
def inventory_page():
    categories = Category.query.all()
    # Get only raw materials from item_master
    rm_type_id = get_rm_type_id()
    if rm_type_id:
        raw_materials = ItemMaster.query.filter(ItemMaster.item_type_id == rm_type_id).order_by(ItemMaster.item_code).all()
    else:
        raw_materials = []
    return render_template('inventory/list.html', categories=categories, raw_materials=raw_materials, current_page='inventory')

@inventory_bp.route('/inventory/create', methods=['GET', 'POST'])
def create_inventory():
    if request.method == 'POST':
        try:
            # Extract form data
            price_per_kg = float(request.form['price_per_kg'])
            soh = float(request.form['soh'])
            monday = float(request.form['monday'])
            tuesday = float(request.form['tuesday'])
            wednesday = float(request.form['wednesday'])
            thursday = float(request.form['thursday'])
            friday = float(request.form['friday'])
            monday2 = float(request.form['monday2'])
            tuesday2 = float(request.form['tuesday2'])
            wednesday2 = float(request.form['wednesday2'])
            thursday2 = float(request.form['thursday2'])
            friday2 = float(request.form['friday2'])

            # Calculate derived fields for validation (optional)
            total_required = monday + tuesday + wednesday + thursday + friday

            inventory = Inventory(
                week_commencing=datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date(),
                category_id=int(request.form['category_id']),
                raw_material_id=int(request.form['raw_material_id']),
                price_per_kg=price_per_kg,
                total_required=total_required,
                soh=soh,
                monday=monday,
                tuesday=tuesday,
                wednesday=wednesday,
                thursday=thursday,
                friday=friday,
                monday2=monday2,
                tuesday2=tuesday2,
                wednesday2=wednesday2,
                thursday2=thursday2,
                friday2=friday2
            )
            db.session.add(inventory)
            db.session.commit()
            flash('Inventory record created successfully!', 'success')
            return redirect(url_for('inventory.inventory_page'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating inventory record: {str(e)}', 'error')

    categories = Category.query.all()
    # Get only raw materials from item_master
    rm_type_id = get_rm_type_id()
    if rm_type_id:
        raw_materials = ItemMaster.query.filter(ItemMaster.item_type_id == rm_type_id).order_by(ItemMaster.item_code).all()
    else:
        raw_materials = []
    productions = Production.query.all()
    return render_template('inventory/create.html', categories=categories, raw_materials=raw_materials, productions=productions, current_page='inventory')

@inventory_bp.route('/inventory/edit/<int:id>', methods=['GET', 'POST'])
def edit_inventory(id):
    inventory = Inventory.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Ensure all required fields are present
            required_fields = [
                'week_commencing', 'category_id', 'raw_material_id', 'price_per_kg', 'soh',
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                'monday2', 'tuesday2', 'wednesday2', 'thursday2', 'friday2'
            ]
            for field in required_fields:
                if field not in request.form or request.form[field] == '':
                    flash(f'Missing required field: {field}', 'error')
                    return redirect(request.url)

            # Extract form data
            price_per_kg = float(request.form['price_per_kg'])
            soh = float(request.form['soh'])
            monday = float(request.form['monday'])
            tuesday = float(request.form['tuesday'])
            wednesday = float(request.form['wednesday'])
            thursday = float(request.form['thursday'])
            friday = float(request.form['friday'])
            monday2 = float(request.form['monday2'])
            tuesday2 = float(request.form['tuesday2'])
            wednesday2 = float(request.form['wednesday2'])
            thursday2 = float(request.form['thursday2'])
            friday2 = float(request.form['friday2'])

            # Calculate derived fields for validation (optional)
            total_required = monday + tuesday + wednesday + thursday + friday

            # Update fields
            inventory.week_commencing = datetime.strptime(request.form['week_commencing'], '%Y-%m-%d').date()
            inventory.category_id = int(request.form['category_id'])
            inventory.raw_material_id = int(request.form['raw_material_id'])
            inventory.price_per_kg = price_per_kg
            inventory.total_required = total_required
            inventory.soh = soh
            inventory.monday = monday
            inventory.tuesday = tuesday
            inventory.wednesday = wednesday
            inventory.thursday = thursday
            inventory.friday = friday
            inventory.monday2 = monday2
            inventory.tuesday2 = tuesday2
            inventory.wednesday2 = wednesday2
            inventory.thursday2 = thursday2
            inventory.friday2 = friday2
            
            db.session.commit()
            flash('Inventory updated successfully!', 'success')
            return redirect(url_for('inventory.inventory_page'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating inventory record: {str(e)}', 'error')
            return redirect(request.url)

    categories = Category.query.all()
    # Get only raw materials from item_master
    rm_type_id = get_rm_type_id()
    if rm_type_id:
        raw_materials = ItemMaster.query.filter(ItemMaster.item_type_id == rm_type_id).order_by(ItemMaster.item_code).all()
    else:
        raw_materials = []
    productions = Production.query.all()
    return render_template('inventory/edit.html', inventory=inventory, categories=categories, raw_materials=raw_materials, productions=productions)

@inventory_bp.route('/inventory/delete/<int:id>', methods=['POST'])
def delete_inventory(id):
    inventory = Inventory.query.get_or_404(id)
    try:
        db.session.delete(inventory)
        db.session.commit()
        flash('Inventory record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting inventory record: {str(e)}', 'error')
    return redirect(url_for('inventory.inventory_page'))

@inventory_bp.route('/inventory/get_category_options', methods=['GET'])
def get_category_options():
    try:
        categories = Category.query.all()
        data = [{'id': category.id, 'name': category.name} for category in categories]
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/inventory/get_raw_material_options', methods=['GET'])
def get_raw_material_options():
    try:
        # Get only raw materials from item_master
        rm_type_id = get_rm_type_id()
        if rm_type_id:
            raw_materials = ItemMaster.query.filter(ItemMaster.item_type_id == rm_type_id).all()
        else:
            raw_materials = []
        data = [{'id': raw_material.id, 'name': raw_material.description or raw_material.item_code} for raw_material in raw_materials]
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/inventory/get_search_inventories', methods=['GET'])
def get_search_inventories():
    try:
        query = Inventory.query
        week_commencing = request.args.get('week_commencing')
        category_id = request.args.get('category')
        raw_material_id = request.args.get('raw_material')

        if week_commencing:
            try:
                week_commencing = datetime.strptime(week_commencing, '%Y-%m-%d').date()
                query = query.filter(Inventory.week_commencing == week_commencing)
            except ValueError:
                return jsonify({'error': 'Invalid week commencing date format'}), 400

        if category_id:
            query = query.filter(Inventory.category_id == int(category_id))

        if raw_material_id:
            query = query.filter(Inventory.raw_material_id == int(raw_material_id))

        inventories = query.all()
        data = [{
            'id': inv.id,
            'week_commencing': inv.week_commencing.strftime('%Y-%m-%d') if inv.week_commencing else '',
            'category_name': inv.category.name if inv.category else '',
            'raw_material_name': inv.raw_material.description or inv.raw_material.item_code if inv.raw_material else '',
            'price_per_kg': inv.price_per_kg,
            'soh': inv.soh,
            'value_soh': inv.value_soh,  # Use property
            'monday': inv.monday,
            'tuesday': inv.tuesday,
            'wednesday': inv.wednesday,
            'thursday': inv.thursday,
            'friday': inv.friday,
            'total_required': inv.total_required or 0,
            'total_to_be_ordered': inv.total_to_be_ordered or 0,  # Use property
            'monday2': inv.monday2,
            'tuesday2': inv.tuesday2,
            'wednesday2': inv.wednesday2,
            'thursday2': inv.thursday2,
            'friday2': inv.friday2,
            'variance': inv.variance or 0,  # Use property
            'value_to_be_ordered': inv.value_to_be_ordered or 0  # Use property
        } for inv in inventories]
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/inventory/export_inventories', methods=['GET'])
def export_inventories():
    try:
        query = Inventory.query
        week_commencing = request.args.get('week_commencing')
        category_id = request.args.get('category')
        raw_material_id = request.args.get('raw_material')

        if week_commencing:
            try:
                week_commencing = datetime.strptime(week_commencing, '%Y-%m-%d').date()
                query = query.filter(Inventory.week_commencing == week_commencing)
            except ValueError:
                return jsonify({'error': 'Invalid week commencing date format'}), 400

        if category_id:
            query = query.filter(Inventory.category_id == int(category_id))

        if raw_material_id:
            query = query.filter(Inventory.raw_material_id == int(raw_material_id))

        inventories = query.all()
        data = [{
            'Week Commencing': inv.week_commencing.strftime('%Y-%m-%d') if inv.week_commencing else '',
            'Category': inv.category.name if inv.category else '',
            'Raw Material': inv.raw_material.description or inv.raw_material.item_code if inv.raw_material else '',
            'Price per kg': inv.price_per_kg,
            'Total Required': inv.total_required,
            'SOH': inv.soh,
            'Value SOH': inv.value_soh,  # Use property
            'Monday': inv.monday,
            'Tuesday': inv.tuesday,
            'Wednesday': inv.wednesday,
            'Thursday': inv.thursday,
            'Friday': inv.friday,
            'Total to be Ordered': inv.total_to_be_ordered,  # Use property
            'Monday2': inv.monday2,
            'Tuesday2': inv.tuesday2,
            'Wednesday2': inv.wednesday2,
            'Thursday2': inv.thursday2,
            'Friday2': inv.friday2,
            'Variance': inv.variance,  # Use property
            'Value to be Ordered': inv.value_to_be_ordered  # Use property
        } for inv in inventories]

        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Inventory', index=False)
        output.seek(0)

        return Response(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment;filename=inventory_export.xlsx'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/inventory/get_data', methods=['GET'])
def get_inventory_data():
    try:
        # Get filter parameters
        category_id = request.args.get('category')
        raw_material_id = request.args.get('raw_material')
        week_commencing = request.args.get('week_commencing')
        
        # Base query with joins to get related data
        query = db.session.query(
            Inventory,
            Category.name.label('category_name'),
            ItemMaster.description.label('raw_material_name')
        ).join(
            Category, Inventory.category_id == Category.id
        ).join(
            ItemMaster, Inventory.raw_material_id == ItemMaster.id
        )
        
        # Apply filters
        if category_id:
            query = query.filter(Inventory.category_id == int(category_id))
        if raw_material_id:
            query = query.filter(Inventory.raw_material_id == int(raw_material_id))
        if week_commencing:
            week_date = datetime.strptime(week_commencing, '%Y-%m-%d').date()
            query = query.filter(Inventory.week_commencing == week_date)
        
        results = query.all()
        
        # Convert to list of dictionaries
        data = []
        for inventory, category_name, raw_material_name in results:
            data.append({
                'id': inventory.id,
                'week_commencing': inventory.week_commencing.strftime('%Y-%m-%d'),
                'category_name': category_name,
                'raw_material_name': raw_material_name,
                'price_per_kg': inventory.price_per_kg,
                'total_required': inventory.total_required,
                'soh': inventory.soh,
                'monday': inventory.monday,
                'tuesday': inventory.tuesday,
                'wednesday': inventory.wednesday,
                'thursday': inventory.thursday,
                'friday': inventory.friday,
                'monday2': inventory.monday2,
                'tuesday2': inventory.tuesday2,
                'wednesday2': inventory.wednesday2,
                'thursday2': inventory.thursday2,
                'friday2': inventory.friday2,
                'value_soh': inventory.value_soh,
                'total_to_be_ordered': inventory.total_to_be_ordered,
                'variance': inventory.variance,
                'value_to_be_ordered': inventory.value_to_be_ordered
            })
        
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/inventory/get_chart_data', methods=['GET'])
def get_chart_data():
    try:
        # Get filter parameters
        category_id = request.args.get('category')
        raw_material_id = request.args.get('raw_material')
        
        # Base query
        query = db.session.query(
            Inventory,
            Category.name.label('category_name'),
            ItemMaster.description.label('raw_material_name')
        ).join(
            Category, Inventory.category_id == Category.id
        ).join(
            ItemMaster, Inventory.raw_material_id == ItemMaster.id
        )
        
        # Apply filters
        if category_id:
            query = query.filter(Inventory.category_id == int(category_id))
        if raw_material_id:
            query = query.filter(Inventory.raw_material_id == int(raw_material_id))
        
        results = query.all()
        
        # Process data for chart
        chart_data = {
            'labels': [],
            'datasets': [{
                'label': 'SOH Value',
                'data': [],
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            }]
        }
        
        for inventory, category_name, raw_material_name in results:
            chart_data['labels'].append(f"{raw_material_name} - {inventory.week_commencing.strftime('%Y-%m-%d')}")
            chart_data['datasets'][0]['data'].append(inventory.value_soh)
        
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500