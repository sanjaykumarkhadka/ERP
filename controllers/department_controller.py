from flask import Blueprint, request, jsonify
from flask import flash, redirect, url_for
from models.department import Department
from database import db
import sqlalchemy

department_bp = Blueprint('department', __name__)

@department_bp.route('/department', methods=['GET'])
def department_list():
    departments = Department.query.all()
    return jsonify([{'departmentName': dept.departmentName, 'id': dept.department_id} for dept in departments])

@department_bp.route('/department', methods=['POST'])
def department_save():
    try:
        data = request.get_json()
        new_department = Department(departmentName=data['departmentName'])
        db.session.add(new_department)
        db.session.commit()
        return jsonify({'message': 'Department saved successfully!', 'id': new_department.department_id}), 200
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Department name already exists'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@department_bp.route('/add_department', methods=['POST'])
def add_department():
        try:
            department_id = request.form['departmentID']
            department_name = request.form['departmentName']
            new_department = Department(departmentID=department_id, departmentName=department_name)
            db.session.add(new_department)
            db.session.commit()
            flash('Department added successfully!', 'success')
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()
            flash('Department ID already exists.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding department: {e}', 'error')
        return redirect(url_for('item_master'))