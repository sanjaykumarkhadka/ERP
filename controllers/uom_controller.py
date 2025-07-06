from flask import Blueprint, request, jsonify
from models.uom import UOM
from database import db
import sqlalchemy

uom_bp = Blueprint('uom', __name__)

@uom_bp.route('/uom', methods=['GET'])
def uom_list():
    uoms = UOM.query.all()
    return jsonify([{'UOMName': uom.UOMName, 'id': uom.UOMID} for uom in uoms])

@uom_bp.route('/uom', methods=['POST'])
def uom_save():
    try:
        data = request.get_json()
        new_uom = UOM(UOMName=data['UOMName'])
        db.session.add(new_uom)
        db.session.commit()
        return jsonify({'message': 'UOM saved successfully!', 'id': new_uom.UOMID}), 200
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'UOM name already exists'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 