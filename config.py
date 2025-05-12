import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'basma'
    
    MYSQL_USER = 'act4_user' 
    MYSQL_PASSWORD = '' # <--- VÉRIFIEZ ET METTEZ VOTRE VRAI MOT DE PASSE
    MYSQL_HOST = 'localhost'
    MYSQL_DB = 'act4community_db'
    MYSQL_CHARSET = 'utf8mb4'

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}?charset={MYSQL_CHARSET}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'act4community/uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}