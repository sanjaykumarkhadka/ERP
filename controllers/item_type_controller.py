from flask import Blueprint, render_template, request, jsonify
from database import db
from models.item_type import ItemType

item_type_bp = Blueprint('item_type', __name__)

@item_type_bp.route('/item-type', methods=['GET'])
def item_type_list():
    item_types = ItemType.query.all()
    return jsonify([{'type_name': item.type_name, 'id': item.id} for item in item_types])

@item_type_bp.route('/item-type/create', methods=['GET'])
def item_type_create():
    return render_template('item_type/create.html')

@item_type_bp.route('/item-type', methods=['POST'])
def item_type_save():
    try:
        data = request.get_json()
        new_item_type = ItemType(type_name=data['type_name'])
        db.session.add(new_item_type)
        db.session.commit()
        return jsonify({'message': 'Item type saved successfully!', 'id': new_item_type.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@item_type_bp.route('/item-type/edit/<int:id>', methods=['GET'])
def item_type_edit(id):
    item_type = ItemType.query.get_or_404(id)
    return render_template('item_type/edit.html', item_type=item_type)

@item_type_bp.route('/item-type/<int:id>', methods=['PUT'])
def item_type_update(id):
    try:
        item_type = ItemType.query.get_or_404(id)
        data = request.get_json()
        item_type.type_name = data['type_name']
        db.session.commit()
        return jsonify({'message': 'Item type updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@item_type_bp.route('/item-type/<int:id>', methods=['DELETE'])
def item_type_delete(id):
    try:
        item_type = ItemType.query.get_or_404(id)
        db.session.delete(item_type)
        db.session.commit()
        return jsonify({'message': 'Item type deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500