from flask import Blueprint, request, jsonify
from flask import flash, redirect, url_for
from models.category import Category
from database import db
import sqlalchemy

category_bp = Blueprint('category', __name__)

@category_bp.route('/category', methods=['GET'])
def category_list():
    categories = Category.query.all()
    return jsonify([{'name': category.name, 'id': category.id} for category in categories])

@category_bp.route('/category', methods=['POST'])
def category_save():
    try:
        data = request.get_json()
        new_category = Category(name=data['name'])
        db.session.add(new_category)
        db.session.commit()
        return jsonify({'message': 'Category saved successfully!', 'id': new_category.id}), 200
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Category name already exists'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@category_bp.route('/add_category', methods=['POST'])
def add_category():
    try:
        category_id = request.form['categoryID']
        category_name = request.form['categoryName']
        new_category = Category(categoryID=category_id, categoryName=category_name)
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully!', 'success')
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
        flash('Category ID already exists.', 'error')