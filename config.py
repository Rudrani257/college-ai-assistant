# config.py - Configuration settings for the Flask application

import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/college_ai_db')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    COLLEGE_NAME = "Bharat College of Engineering"
    COLLEGE_SHORT = "BCOE"
    COLLEGE_LOCATION = "Badlapur, Maharashtra"
    COLLEGE_PHONE = "+91-712-2806400"
    COLLEGE_EMAIL = "info@bcoe.edu"
    COLLEGE_WEBSITE = "www.bcoe.edu"