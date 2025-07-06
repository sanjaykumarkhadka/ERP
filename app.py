from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from dotenv import load_dotenv
import os
import sqlalchemy.exc
from datetime import datetime
from flask_migrate import Migrate

# Import the single SQLAlchemy instance
from database import db


def create_app():
    # Load environment variables from .env file
    load_dotenv()

    # File upload configuration
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

    

    # Create uploads directory if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Create and configure the Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Validate SQLALCHEMY_DATABASE_URI
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise RuntimeError(
            "SQLALCHEMY_DATABASE_URI is not set. Please define it in the .env file or environment variables."
        )

    # Initialize SQLAlchemy with the app
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register Blueprints
    # from controllers.joining_controller import joining_bp  # REMOVED - joining table deprecated
    from controllers.soh_controller import soh_bp
    from controllers.ingredients_controller import ingredients_bp
    from controllers.packing_controller import packing
    from controllers.filling_controller import filling_bp
    from controllers.production_controller import production_bp
    from controllers.recipe_controller import recipe_bp
    from controllers.inventory_controller import inventory_bp
    from controllers.department_controller import department_bp
    from controllers.machinery_controller import machinery_bp
    from controllers.category_controller import category_bp
    from controllers.item_master_controller import item_master_bp
    from controllers.item_type_controller import item_type_bp
    from controllers.uom_controller import uom_bp
    from controllers.login_controller import login_bp

    app.register_blueprint(soh_bp)
    app.register_blueprint(ingredients_bp)
    app.register_blueprint(packing)
    app.register_blueprint(filling_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(recipe_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(machinery_bp)    
    app.register_blueprint(category_bp)
    app.register_blueprint(item_master_bp)
    app.register_blueprint(item_type_bp)
    app.register_blueprint(uom_bp)
    app.register_blueprint(login_bp)

    # Import models
    from models import soh, finished_goods, item_master, recipe_master, usage_report
    # from models import joining  # REMOVED - joining table deprecated
    from models import machinery, department, category, production, packing, filling, allergen
    # joining_allergen removed - table dropped
    

    @app.template_filter('format_date')
    def format_date(value):
        """Convert date to DD-MM-YYYY format"""
        if not value:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return value
        return value.strftime('%d-%m-%Y') if value else ''
    
    # Authentication middleware
    @app.before_request
    def require_login():
        # Allow access to login, register, and static files without authentication
        allowed_routes = ['login.login', 'login.register', 'login.check_username', 'login.check_email', 'static']
        
        if request.endpoint in allowed_routes:
            return
        
        # Check if user is logged in
        if 'user_id' not in session:
            # For AJAX requests, return JSON error instead of redirect
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({'success': False, 'error': 'Authentication required. Please log in.'}), 401
            return redirect(url_for('login.login'))
    
    # Define routes
    @app.route('/') 
    def index():
        return render_template('index.html', current_page="home")

    # Database tables already exist - no need to create them
    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)