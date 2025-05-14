from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from act4community import db # Import 'db' depuis __init__.py
from datetime import datetime # Assurez-vous que datetime est importé


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False, default='candidat')
    
    projects = db.relationship('Project', backref='applicant', lazy=True, foreign_keys='Project.user_id')
    evaluations = db.relationship('Evaluation', backref='evaluator', lazy=True, foreign_keys='Evaluation.evaluator_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash:
             return check_password_hash(self.password_hash, password)
        return False

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    submission_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False, default='Soumis')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    budget_estime = db.Column(db.Float, nullable=True)
    localisation = db.Column(db.String(200), nullable=True)
    date_debut_prevue = db.Column(db.Date, nullable=True)
    duree_estimee = db.Column(db.String(100), nullable=True)
    objectifs_specifiques = db.Column(db.Text, nullable=True)
    
    appointment_date = db.Column(db.DateTime, nullable=True)
    appointment_location = db.Column(db.String(250), nullable=True, default="Bureaux Act4Community [Ville]")
    appointment_notes = db.Column(db.Text, nullable=True, default="Veuillez apporter une copie de votre pièce d'identité et tout document original pertinent à votre projet.")

    documents = db.relationship('Document', backref='project', lazy=True, cascade="all, delete-orphan")
    evaluations = db.relationship('Evaluation', backref='project_evaluated', lazy=True, cascade="all, delete-orphan", foreign_keys='Evaluation.project_id')

    def __repr__(self):
        return f'<Project {self.title}>'

class Document(db.Model):
    __tablename__ = 'document'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(300), nullable=False) 
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

    def __repr__(self):
        return f'<Document {self.filename}>'

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    score = db.Column(db.Integer) 
    comments = db.Column(db.Text)
    evaluation_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Evaluation for Project {self.project_id} by User {self.evaluator_id}>'


# DANS act4community/models.py
# ... (User, Project, Document, Evaluation restent identiques) ...


class MessageContact(db.Model):
    __tablename__ = 'message_contact'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False) # Nom de l'expéditeur
    email = db.Column(db.String(150), nullable=False) # Email de l'expéditeur
    subject = db.Column(db.String(200), nullable=False)
    message_body = db.Column(db.Text, nullable=False)
    attachment_filename = db.Column(db.String(250), nullable=True) # Nom du fichier original
    attachment_filepath = db.Column(db.String(300), nullable=True) # Chemin vers le fichier stocké
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Lié à un user si connecté
    is_read_by_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Relation si vous voulez accéder à l'utilisateur depuis le message
    # backref est optionnel si vous n'avez pas besoin de user.contact_messages_sent
    sender = db.relationship('User', backref='sent_contact_messages') 

    def __repr__(self):
        return f'<MessageContact {self.id} de {self.email} - Objet: {self.subject[:30]}>'