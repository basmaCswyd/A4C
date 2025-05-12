import os
import pymysql
import datetime # Pour le context processor 'now'
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config # Importer la configuration

# Initialisation des extensions SANS l'application pour l'instant
pymysql.install_as_MySQLdb()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login' # 'main' est le nom du Blueprint
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

def create_app(config_class=Config):
    """Factory pour créer et configurer l'application Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Lier les extensions à l'application créée
    db.init_app(app)
    login_manager.init_app(app)

    # Créer le dossier uploads s'il n'existe pas
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Context processor pour injecter 'now' dans les templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.utcnow} 

    # Importations des parties de l'application APRÈS l'initialisation de 'app' et 'db'
    # pour éviter les imports circulaires et les problèmes de contexte.
    
    # Enregistrer les modèles avec l'application
    # L'importation de models.py ici exécutera la définition des classes de modèles
    # et les liera à l'instance 'db' qui est maintenant configurée avec 'app'.
    with app.app_context():
        from . import models 

    # Importer et enregistrer les Blueprints (qui peuvent utiliser les modèles)
    from act4community.routes import main_bp 
    app.register_blueprint(main_bp)

    # Commandes CLI
    @app.cli.command("init-db")
    def init_db_command():
        """Crée les tables de la base de données."""
        with app.app_context(): 
            # db.drop_all() # Optionnel : pour supprimer avant de recréer, utile en dev
            db.create_all()
        print("Base de données initialisée et tables créées!")

    @app.cli.command("create-admin")
    def create_admin_command():
        """Crée un utilisateur admin."""
        with app.app_context():
            # L'import local de User est bon ici
            from act4community.models import User 
            if User.query.filter_by(role='admin').first():
                print("Un admin existe déjà.")
                return
            
            username = input("Nom d'utilisateur Admin: ")
            email = input("Email Admin: ")
            password = input("Mot de passe Admin: ")
            
            admin = User(username=username, email=email, role='admin')
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin {username} créé avec succès.")

    return app