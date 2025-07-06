from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.user import User
from models.department import Department
from database import db
from datetime import datetime
import re

login_bp = Blueprint('login', __name__)

def is_valid_email(email):
    """Check if email format is valid"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """Check if password meets minimum requirements"""
    return len(password) >= 6

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account is inactive. Please contact an administrator.', 'error')
                return render_template('auth/login.html')
            
            session['user_id'] = user.id
            session['username'] = user.username
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@login_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login.login'))

@login_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return render_template('auth/register.html')
        
        if not is_valid_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('auth/register.html')
        
        if not is_valid_password(password):
            flash('Password must be at least 6 characters long', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/register.html')

@login_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash('Please login to change password', 'error')
        return redirect(url_for('login.login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('auth/change_password.html')
        
        user = User.query.get(session['user_id'])
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('login.login'))
        
        if not user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return render_template('auth/change_password.html')
        
        if not is_valid_password(new_password):
            flash('New password must be at least 6 characters long', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('auth/change_password.html')
        
        if current_password == new_password:
            flash('New password must be different from current password', 'error')
            return render_template('auth/change_password.html')
        
        try:
            user.set_password(new_password)
            user.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while changing password. Please try again.', 'error')
    
    return render_template('auth/change_password.html')

@login_bp.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        flash('Please login to view profile', 'error')
        return redirect(url_for('login.login'))
    
    user = User.query.get_or_404(session['user_id'])
    departments = Department.query.all()
    
    return render_template('auth/profile.html', user=user, departments=departments)

@login_bp.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash('Please login to update profile', 'error')
        return redirect(url_for('login.login'))
    
    user = User.query.get_or_404(session['user_id'])
    
    try:
        # Update email
        email = request.form.get('email', '').strip()
        if email != user.email:
            if not is_valid_email(email):
                flash('Please enter a valid email address', 'error')
                return redirect(url_for('login.profile'))
            if User.query.filter(User.id != user.id, User.email == email).first():
                flash('Email already registered', 'error')
                return redirect(url_for('login.profile'))
            user.email = email
        
        # Update department
        department_id = request.form.get('department_id')
        user.department_id = int(department_id) if department_id else None
        
        # Update mobile
        mobile = request.form.get('mobile', '').strip()
        user.mobile = mobile if mobile else None
        
        # Update start date
        start_date = request.form.get('start_date')
        user.start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        
        # Update status
        user.is_active = bool(request.form.get('is_active'))
        
        # Update timestamp
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('login.profile'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating profile. Please try again.', 'error')
        return redirect(url_for('login.profile'))

@login_bp.route('/check-username')
def check_username():
    """AJAX endpoint to check if username is available"""
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'available': False, 'message': 'Username is required'})
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'available': False, 'message': 'Username already exists'})
    
    return jsonify({'available': True, 'message': 'Username is available'})

@login_bp.route('/check-email')
def check_email():
    """AJAX endpoint to check if email is available"""
    email = request.args.get('email', '').strip()
    if not email:
        return jsonify({'available': False, 'message': 'Email is required'})
    
    if not is_valid_email(email):
        return jsonify({'available': False, 'message': 'Invalid email format'})
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'available': False, 'message': 'Email already registered'})
    
    return jsonify({'available': True, 'message': 'Email is available'}) 