from flask_sqlalchemy import SQLAlchemy

# Create a single SQLAlchemy instance to be used across the application
db = SQLAlchemy()

# Make the base model class available
Base = db.Model