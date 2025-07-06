from flask import Blueprint, request, jsonify
from flask import flash, redirect, url_for
from models.machinery import Machinery
from database import db
import sqlalchemy

machinery_bp = Blueprint('machinery', __name__)

@machinery_bp.route('/machinery', methods=['GET'])
def machinery_list():
    machinery = Machinery.query.all()
    return jsonify([{'machineryName': machine.machineryName, 'id': machine.machineID} for machine in machinery])

@machinery_bp.route('/machinery', methods=['POST'])
def machinery_save():
    try:
        data = request.get_json()
        new_machinery = Machinery(machineryName=data['machineryName'])
        db.session.add(new_machinery)
        db.session.commit()
        return jsonify({'message': 'Machinery saved successfully!', 'id': new_machinery.machineID}), 200
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Machinery name already exists'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@machinery_bp.route('/add_machine', methods=['POST'])        
def add_machine():
        try:
            machine_id = request.form['machineID']
            machinery_name = request.form['machineryName']
            new_machine = Machinery(machineID=machine_id, machineryName=machinery_name)
            db.session.add(new_machine)
            db.session.commit()
            flash('Machine added successfully!', 'success')
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            flash('Machine ID already exists.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding machine: {e}', 'error')
        return redirect(url_for('item_master'))
