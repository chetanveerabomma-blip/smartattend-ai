import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smartattend-ai-dev-secret-key-98234871923'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(basedir, 'smartattend.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    
    # Target Attendance Thresholds
    TARGET_PERCENTAGE = 75.0
    CONDONABLE_MIN_PERCENTAGE = 65.0
