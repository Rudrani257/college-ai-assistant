# app.py - Main Flask application entry point

from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from config import Config
from models import mongo, bcrypt, seed_database
from routes import main_bp, student_bp, admin_bp
import os

def create_app():
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    mongo.init_app(app)
    bcrypt.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    # Template filters
    @app.template_filter('strftime')
    def strftime_filter(value, format='%d %b %Y'):
        """Format datetime in templates"""
        if isinstance(value, str):
            try:
                from datetime import datetime
                value = datetime.strptime(value, '%Y-%m-%d')
            except:
                return value
        try:
            return value.strftime(format)
        except:
            return str(value)

    @app.template_filter('objectid')
    def objectid_filter(value):
        """Convert ObjectId to string"""
        return str(value)

    return app


# Create app instance
app = create_app()

if __name__ == '__main__':
    # Seed database on first run
    seed_database(app)
    print("🚀 Starting College AI Assistant...")
    print("📌 Open: http://127.0.0.1:5000")
    print("👤 Admin Login: ADMIN001 / admin123")
    print("🎓 Student Login: STU001 / student123")
    app.run(debug=True, host='0.0.0.0', port=5000)