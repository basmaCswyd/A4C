from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectField, IntegerField, FloatField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from flask_wtf.file import FileAllowed
from act4community.models import User # Assurez-vous que l'import est correct
from wtforms import DateTimeLocalField

class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Rôle', choices=[('candidat', 'Candidat'), ('membre_a4c', 'Membre A4C')], default='candidat')
    submit = SubmitField('S\'inscrire')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class ProjectSubmissionForm(FlaskForm):
    title = StringField('Titre du projet', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description détaillée du projet', validators=[DataRequired()])
    
    # --- NOUVEAUX CHAMPS ---
    budget_estime = FloatField('Budget Estimé (€)', validators=[Optional(), NumberRange(min=0)])
    localisation = StringField('Localisation Prévue (Ville/Quartier)', validators=[Optional(), Length(max=200)])
    date_debut_prevue = DateField('Date de Début Prévue', format='%Y-%m-%d', validators=[Optional()])
    duree_estimee = StringField('Durée Estimée (ex: 3 mois)', validators=[Optional(), Length(max=100)])
    objectifs_specifiques = TextAreaField('Objectifs Spécifiques (listez-les)', validators=[Optional()])
    # --- FIN NOUVEAUX CHAMPS ---
    
    documents = FileField('Documents Additionnels (PDF, DOCX)', validators=[Optional(), FileAllowed(['pdf', 'docx', 'doc'], 'Seuls les PDF et DOCX sont autorisés!')])
    submit = SubmitField('Soumettre le projet')

class EvaluationForm(FlaskForm):
    score = IntegerField('Score (1-5)', validators=[DataRequired()])
    comments = TextAreaField('Commentaires', validators=[DataRequired()])
    submit = SubmitField('Soumettre l\'évaluation')



# ... (RegistrationForm, LoginForm, ProjectSubmissionForm, EvaluationForm restent identiques) ...

class SetAppointmentForm(FlaskForm):
    appointment_date = DateTimeLocalField(
        'Date et Heure du Rendez-vous', 
        format='%Y-%m-%dT%H:%M', # Format attendu par le widget HTML5 datetime-local
        validators=[DataRequired(message="Veuillez spécifier une date et une heure.")]
    )
    appointment_location = StringField(
        'Lieu du Rendez-vous', 
        validators=[DataRequired(message="Veuillez spécifier un lieu.")],
        default="Bureaux Act4Community [Ville à préciser]"
    )
    appointment_notes = TextAreaField(
        'Documents à apporter et remarques supplémentaires (cette fiche de convocation est obligatoire)',
        validators=[DataRequired(message="Veuillez ajouter des notes pour le candidat.")],
        default="Veuillez apporter une copie de votre pièce d'identité, tout document original pertinent à votre projet, ainsi que cette fiche de convocation imprimée qui est OBLIGATOIRE pour l'entretien."
    )
    submit = SubmitField('Enregistrer le Rendez-vous et Générer la Convocation')