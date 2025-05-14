import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app, make_response
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from functools import wraps
from weasyprint import HTML, CSS # Pour la génération de PDF
from flask_mail import Message as MailMessage

from act4community import db, login_manager 
from act4community.models import User, Project, Document, Evaluation, MessageContact
from datetime import datetime
from act4community.forms import (
    RegistrationForm, LoginForm, 
    ProjectSubmissionForm, EvaluationForm, 
    SetAppointmentForm, ContactForm # Importer le nouveau formulaire
)


main_bp = Blueprint('main', __name__)

@login_manager.user_loader 
def load_user(user_id):
    try:
        user_id_int = int(user_id)
    except ValueError:
        return None
    return User.query.get(user_id_int)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# --- Décorateurs pour les rôles ---
def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                 flash("Veuillez vous connecter pour accéder à cette page.", "warning")
                 return redirect(url_for('main.login', next=request.url))
            if current_user.role != role_name:
                flash(f"Accès non autorisé. Réservé aux {role_name}s.", "danger")
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def roles_required(role_names):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                 flash("Veuillez vous connecter pour accéder à cette page.", "warning")
                 return redirect(url_for('main.login', next=request.url))
            if current_user.role not in role_names:
                flash(f"Accès non autorisé. Réservé aux rôles: {', '.join(role_names)}.", "danger")
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Routes Générales ---
@main_bp.route('/')
def index():
    return render_template('index.html', title='Accueil')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Votre compte a été créé ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur enregistrement utilisateur: {e}")
            flash(f'Erreur lors de la création du compte. Veuillez réessayer.', 'danger')
    return render_template('register.html', title='S\'inscrire', form=form)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Connexion réussie !', 'success')
            next_page = request.args.get('next')
            if user.role == 'admin':
                return redirect(next_page or url_for('main.admin_dashboard'))
            elif user.role == 'membre_a4c':
                 return redirect(next_page or url_for('main.evaluate_projects_list'))
            else: # candidat
                return redirect(next_page or url_for('main.my_projects'))
        else:
            flash('Échec de la connexion. Veuillez vérifier email et mot de passe.', 'danger')
    return render_template('login.html', title='Se connecter', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('main.index'))

# --- Routes Candidat ---
@main_bp.route('/submit_project', methods=['GET', 'POST'])
@login_required
@role_required('candidat')
def submit_project():
    form = ProjectSubmissionForm()
    if form.validate_on_submit():
        project = Project(
            title=form.title.data, 
            description=form.description.data, 
            applicant=current_user,
            budget_estime=form.budget_estime.data,
            localisation=form.localisation.data,
            date_debut_prevue=form.date_debut_prevue.data,
            duree_estimee=form.duree_estimee.data,
            objectifs_specifiques=form.objectifs_specifiques.data,
            status='Soumis'
        )
        db.session.add(project)
        try:
            db.session.flush() 
            file = form.documents.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                project_upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(project.id))
                os.makedirs(project_upload_path, exist_ok=True)
                filepath_on_disk = os.path.join(project_upload_path, filename)
                file.save(filepath_on_disk)
                db_filepath = os.path.join(str(project.id), filename).replace("\\", "/")
                doc = Document(filename=filename, filepath=db_filepath, project_id=project.id)
                db.session.add(doc)
            db.session.commit()
            flash('Votre projet a été soumis avec succès ! Il sera examiné prochainement.', 'success')
            return redirect(url_for('main.my_projects'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur soumission projet: {e}")
            flash(f'Erreur lors de la soumission du projet. Veuillez réessayer.', 'danger')
    return render_template('submit_project.html', title='Soumettre un projet', form=form)

@main_bp.route('/my_projects')
@login_required
@role_required('candidat')
def my_projects():
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.submission_date.desc()).all()
    return render_template('my_projects.html', title='Mes projets soumis', projects=projects)

@main_bp.route('/uploads/<project_id_str>/<filename>')
@login_required
def uploaded_file(project_id_str, filename):
    try:
        project_id = int(project_id_str)
    except ValueError:
         flash("ID de projet invalide.", "danger")
         return redirect(url_for('main.index'))
    project = Project.query.get_or_404(project_id)
    doc = Document.query.filter_by(project_id=project.id, filename=filename).first_or_404()
    if current_user.id == project.user_id or current_user.role in ['membre_a4c', 'admin']:
        safe_filepath = doc.filepath.replace("\\", "/") # Assurer des slashs corrects
        # Le chemin stocké est déjà relatif à UPLOAD_FOLDER
        directory = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
        
        # Mesure de sécurité supplémentaire pour éviter le path traversal
        # (bien que secure_filename fasse déjà beaucoup)
        full_path = os.path.abspath(os.path.join(directory, safe_filepath))
        if not full_path.startswith(directory):
             flash("Tentative d'accès à un fichier invalide.", "danger")
             current_app.logger.warning(f"Tentative de Path Traversal: user {current_user.id}, path {safe_filepath}")
             return redirect(url_for('main.index'))
             
        return send_from_directory(directory, safe_filepath, as_attachment=False)
    else:
        flash("Accès non autorisé à ce document.", "danger")
        return redirect(url_for('main.index'))

# --- Routes Membre A4C ---
@main_bp.route('/evaluate_projects')
@login_required
@role_required('membre_a4c')
def evaluate_projects_list():
    subquery = db.session.query(Evaluation.project_id).filter(Evaluation.evaluator_id == current_user.id).subquery()
    projects_to_evaluate = Project.query.filter(
        Project.status.in_(['Soumis', 'En évaluation']),
        Project.id.notin_(db.select(subquery.c.project_id))
    ).order_by(Project.submission_date).all()
    return render_template('evaluate_projects_list.html', title='Projets à évaluer', projects=projects_to_evaluate)

@main_bp.route('/evaluate_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
@role_required('membre_a4c')
def evaluate_project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    existing_evaluation = Evaluation.query.filter_by(project_id=project.id, evaluator_id=current_user.id).first()
    if existing_evaluation:
        flash("Vous avez déjà évalué ce projet.", "info")
        return redirect(url_for('main.evaluate_projects_list'))
    if project.status not in ['Soumis', 'En évaluation']:
         flash("Ce projet n'est plus en attente d'évaluation.", "warning")
         return redirect(url_for('main.evaluate_projects_list'))
    form = EvaluationForm()
    if form.validate_on_submit():
        evaluation = Evaluation(
            project_id=project.id,
            evaluator_id=current_user.id,
            score=form.score.data,
            comments=form.comments.data
        )
        db.session.add(evaluation)
        if project.status == 'Soumis':
            project.status = 'En évaluation'
        try:
            db.session.commit()
            flash('Évaluation soumise avec succès.', 'success')
            return redirect(url_for('main.evaluate_projects_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur évaluation projet: {e}")
            flash(f"Erreur lors de la soumission de l'évaluation. Veuillez réessayer.", "danger")
    return render_template('project_detail_evaluation.html', title=f'Évaluer: {project.title}', project=project, form=form)

# --- Routes Admin (et Membre A4C pour stats) ---
@main_bp.route('/statistics')
@login_required
@roles_required(['membre_a4c', 'admin'])
def statistics():
    total_projects_count = Project.query.count()
    projects_by_status = db.session.query(Project.status, db.func.count(Project.status)).group_by(Project.status).all()
    avg_score_query = db.session.query(db.func.avg(Evaluation.score)).scalar()
    average_score = round(avg_score_query, 2) if avg_score_query is not None else "N/A"
    status_counts = dict(projects_by_status)
    return render_template('admin/reports.html', title='Statistiques',
                           total_projects=total_projects_count, 
                           status_counts=status_counts, 
                           average_score=average_score)

@main_bp.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    pending_projects_count = Project.query.filter(Project.status.in_(['Soumis', 'En évaluation'])).count()
    total_users_count = User.query.count()
    total_projects_count = Project.query.count()
    approved_projects_count = Project.query.filter_by(status='Approuvé').count()
    return render_template('admin/dashboard.html', 
                           title='Tableau de bord Admin', 
                           pending_count=pending_projects_count,
                           total_users=total_users_count,
                           total_projects=total_projects_count,
                           approved_projects=approved_projects_count
                           )

@main_bp.route('/admin/users')
@login_required
@role_required('admin')
def manage_users():
    users = User.query.order_by(User.id).all()
    return render_template('admin/manage_users.html', title='Gérer les utilisateurs', users=users)

@main_bp.route('/admin/projects')
@login_required
@role_required('admin')
def admin_manage_projects():
    projects_to_review = Project.query.order_by(
        db.case(
            (Project.status == 'Soumis', 1),
            (Project.status == 'En évaluation', 2),
            (Project.status == 'Approuvé', 3), 
            (Project.status == 'Rejeté', 4),
            else_=5 
        ),
        Project.submission_date.desc()
    ).all()
    return render_template('admin/manage_projects.html', title='Gérer les Projets', projects=projects_to_review) # Changement de titre

@main_bp.route('/admin/project/<int:project_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def admin_approve_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.status in ['Approuvé', 'Rejeté']:
        flash(f'Le projet "{project.title}" a déjà été traité.', 'info')
    else:
        project.status = 'Approuvé'
        try:
            db.session.commit()
            flash(f'Le projet "{project.title}" a été approuvé.', 'success')
        except Exception as e:
             db.session.rollback()
             current_app.logger.error(f"Erreur approbation projet: {e}")
             flash(f'Erreur lors de l\'approbation du projet. Veuillez réessayer.', 'danger')
    return redirect(url_for('main.admin_manage_projects'))

@main_bp.route('/admin/project/<int:project_id>/reject', methods=['POST'])
@login_required
@role_required('admin')
def admin_reject_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.status in ['Approuvé', 'Rejeté']:
        flash(f'Le projet "{project.title}" a déjà été traité.', 'info')
    else:
        project.status = 'Rejeté'
        try:
            db.session.commit()
            flash(f'Le projet "{project.title}" a été rejeté.', 'warning')
        except Exception as e:
             db.session.rollback()
             current_app.logger.error(f"Erreur rejet projet: {e}")
             flash(f'Erreur lors du rejet du projet. Veuillez réessayer.', 'danger')
    return redirect(url_for('main.admin_manage_projects'))

# --- NOUVELLE ROUTE : Définir/Modifier le RDV pour un projet approuvé ---
@main_bp.route('/admin/project/<int:project_id>/set_appointment', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_set_appointment(project_id):
    project = Project.query.get_or_404(project_id)
    if project.status != 'Approuvé':
        flash("Vous ne pouvez définir un rendez-vous que pour les projets approuvés.", "warning")
        return redirect(url_for('main.admin_manage_projects'))

    form = SetAppointmentForm(obj=project) # Pré-remplir avec les données existantes du projet

    if form.validate_on_submit():
        project.appointment_date = form.appointment_date.data
        project.appointment_location = form.appointment_location.data
        project.appointment_notes = form.appointment_notes.data
        try:
            db.session.commit()
            flash(f"Rendez-vous pour le projet '{project.title}' enregistré. Le candidat peut maintenant télécharger sa convocation.", "success")
            return redirect(url_for('main.admin_manage_projects'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur enregistrement RDV projet {project_id}: {e}")
            flash(f"Erreur lors de l'enregistrement du rendez-vous : {e}", "danger")
            
    return render_template('admin/set_appointment.html', title=f"Rendez-vous : {project.title}", form=form, project=project)

# --- NOUVELLE ROUTE : Générer et Télécharger la Convocation PDF ---
@main_bp.route('/project/<int:project_id>/convocation_pdf')
@login_required # Le candidat doit être connecté (ou admin pour test)
def download_convocation_pdf(project_id):
    project = Project.query.get_or_404(project_id)

    if not (current_user.id == project.user_id or current_user.role == 'admin'):
        flash("Accès non autorisé à cette convocation.", "danger")
        return redirect(url_for('main.index'))

    if project.status != 'Approuvé' or not project.appointment_date:
        flash("La convocation n'est pas encore disponible pour ce projet.", "warning")
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_manage_projects'))
        else:
            return redirect(url_for('main.my_projects'))

    logo_url = url_for('static', filename='images/a4c_logo.png', _external=True)
    html_out = render_template('project/convocation_pdf_template.html', project=project, logo_url=logo_url)
    
    # Pour ajouter un CSS spécifique au PDF (optionnel)
    # css_path = os.path.join(current_app.static_folder, 'css', 'pdf_style.css')
    # pdf_css = None
    # if os.path.exists(css_path):
    #     pdf_css = CSS(filename=css_path)
    
    pdf = HTML(string=html_out, base_url=request.url_root).write_pdf() # stylesheets=[pdf_css] si vous utilisez un CSS externe

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    # Rendre le nom de fichier plus simple et sûr
    safe_title = "".join(c if c.isalnum() else "_" for c in project.title[:30]) # Prend les 30 premiers caractères alphanumériques ou _
    response.headers['Content-Disposition'] = f'attachment; filename=convocation_projet_{project.id}_{safe_title}.pdf'
    
    return response

@main_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    user_to_edit = User.query.get_or_404(user_id)
    users_admin_count = User.query.filter_by(role='admin').count()
    if request.method == 'POST':
        new_role = request.form.get('role')
        if new_role in ['candidat', 'membre_a4c', 'admin']:
            if user_to_edit.role == 'admin' and users_admin_count <= 1 and new_role != 'admin':
                 flash('Impossible de modifier le rôle du dernier administrateur. Créez un autre admin d\'abord.', 'danger')
            else:
                 user_to_edit.role = new_role
                 try:
                     db.session.commit()
                     flash(f"Rôle de {user_to_edit.username} mis à jour.", "success")
                 except Exception as e:
                     db.session.rollback()
                     current_app.logger.error(f"Erreur màj rôle user: {e}")
                     flash(f"Erreur lors de la mise à jour du rôle. Veuillez réessayer.", "danger")
        else:
            flash("Rôle invalide.", "danger")
        return redirect(url_for('main.manage_users'))
    return render_template('admin/edit_user.html', 
                           title=f"Modifier : {user_to_edit.username}", 
                           user=user_to_edit, 
                           users_admin_count=users_admin_count)

@main_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id:
        flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
        return redirect(url_for('main.manage_users'))
    if user_to_delete.role == 'admin' and User.query.filter_by(role='admin').count() <= 1:
        flash("Impossible de supprimer le dernier administrateur.", "danger")
        return redirect(url_for('main.manage_users'))
    try:
        Evaluation.query.filter_by(evaluator_id=user_to_delete.id).delete()
        projects_to_delete = Project.query.filter_by(user_id=user_to_delete.id).all()
        for project in projects_to_delete:
             Evaluation.query.filter_by(project_id=project.id).delete()
             db.session.delete(project) # Les documents seront supprimés par cascade
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"Utilisateur {user_to_delete.username} et ses données associées supprimés.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur suppression utilisateur {user_id}: {e}")
        flash(f"Erreur lors de la suppression de l'utilisateur. Consultez les logs.", "danger")
    return redirect(url_for('main.manage_users'))



    # DANS act4community/routes.py

# ... (routes existantes) ...

# --- PAGE DE CONTACT POUR LES UTILISATEURS ---
@main_bp.route('/contact', methods=['GET', 'POST'])
def contact_us():
    form = ContactForm()
    if current_user.is_authenticated and request.method == 'GET':
        # Pré-remplir le nom et l'email si l'utilisateur est connecté
        form.name.data = current_user.username 
        form.email.data = current_user.email

    if form.validate_on_submit():
        attachment_filename = None
        attachment_filepath_db = None

        file = form.attachment.data
        if file and allowed_file(file.filename): # Réutiliser la fonction allowed_file pour les extensions
            # Créer un dossier 'contact_attachments' dans UPLOAD_FOLDER s'il n'existe pas
            contact_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'contact_attachments')
            os.makedirs(contact_upload_dir, exist_ok=True)
            
            original_filename = secure_filename(file.filename)
            # Pour éviter les collisions, on peut préfixer avec un timestamp ou UUID
            timestamp_prefix = datetime.utcnow().strftime('%Y%m%d%H%M%S%f_')
            filename_on_disk = timestamp_prefix + original_filename
            
            filepath_on_disk_full = os.path.join(contact_upload_dir, filename_on_disk)
            file.save(filepath_on_disk_full)
            
            attachment_filename = original_filename # Nom original pour affichage
            attachment_filepath_db = os.path.join('contact_attachments', filename_on_disk).replace("\\", "/") # Chemin relatif à UPLOAD_FOLDER

        new_message = MessageContact(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message_body=form.message_body.data,
            attachment_filename=attachment_filename,
            attachment_filepath=attachment_filepath_db,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(new_message)
        try:
            db.session.commit()
            
            # Optionnel : Envoyer un email de confirmation à l'utilisateur
            # if current_app.config.get('MAIL_SERVER'): # Vérifier si mail est configuré
            #     try:
            #         msg_to_user = MailMessage(
            #             subject="Confirmation de réception de votre message - Act4Community",
            #             sender=current_app.config['MAIL_DEFAULT_SENDER'],
            #             recipients=[new_message.email]
            #         )
            #         msg_to_user.html = render_template(
            #             'email/contact_confirmation_user.html', 
            #             name=new_message.name, 
            #             message_subject=new_message.subject
            #         )
            #         mail.send(msg_to_user)
            #     except Exception as e_mail:
            #         current_app.logger.error(f"Erreur envoi email confirmation contact: {e_mail}")
            #         flash("Votre message a été envoyé, mais nous n'avons pas pu envoyer d'email de confirmation.", "warning")

            # Optionnel : Envoyer une notification à l'admin
            # if current_app.config.get('ADMIN_EMAIL') and current_app.config.get('MAIL_SERVER'):
            #    try:
            #        msg_to_admin = MailMessage(
            #            subject=f"Nouveau Message Contact: {new_message.subject}",
            #            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            #            recipients=[current_app.config['ADMIN_EMAIL']]
            #        )
            #        # Créez un template email/new_contact_message_admin.html si besoin
            #        msg_to_admin.body = f"Nouveau message de {new_message.name} ({new_message.email}).\nObjet: {new_message.subject}\nMessage:\n{new_message.message_body}"
            #        mail.send(msg_to_admin)
            #    except Exception as e_mail_admin:
            #        current_app.logger.error(f"Erreur envoi email notif admin contact: {e_mail_admin}")

            flash("Votre message a été envoyé avec succès ! Nous vous répondrons dès que possible.", "success")
            return redirect(url_for('main.index')) # Ou une page de remerciement
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur sauvegarde message contact: {e}")
            flash(f"Erreur lors de l'envoi du message : {e}. Veuillez réessayer.", "danger")
            
    return render_template('contact.html', title="Contactez-nous", form=form)

# --- MESSAGERIE ADMIN ---
@main_bp.route('/admin/messages')
@login_required
@role_required('admin')
def admin_messages_list():
    page = request.args.get('page', 1, type=int)
    # Trier par non lus en premier, puis par date
    messages = MessageContact.query.order_by(MessageContact.is_read_by_admin.asc(), MessageContact.timestamp.desc()).paginate(page=page, per_page=15)
    return render_template('admin/messages_list.html', title="Messagerie Reçue", messages_pagination=messages)

@main_bp.route('/admin/message/<int:message_id>', methods=['GET', 'POST']) # POST pour marquer comme lu/non lu
@login_required
@role_required('admin')
def admin_message_detail(message_id):
    message = MessageContact.query.get_or_404(message_id)
    
    if request.method == 'POST': # Pourrait être utilisé pour marquer comme lu/non lu
        if 'mark_read' in request.form:
            message.is_read_by_admin = True
            flash("Message marqué comme lu.", "info")
        elif 'mark_unread' in request.form:
            message.is_read_by_admin = False
            flash("Message marqué comme non lu.", "info")
        db.session.commit()
        return redirect(url_for('main.admin_message_detail', message_id=message.id))

    # Marquer automatiquement comme lu lors de la visualisation (sauf si déjà traité par un bouton)
    if not message.is_read_by_admin and request.method == 'GET':
        message.is_read_by_admin = True
        db.session.commit()
        
    return render_template('admin/message_detail.html', title=f"Message de {message.name}", message=message)

# --- Route pour télécharger la pièce jointe d'un message contact ---
@main_bp.route('/admin/message_attachment/<int:message_id>')
@login_required
@role_required('admin')
def download_message_attachment(message_id):
    message = MessageContact.query.get_or_404(message_id)
    if message.attachment_filepath:
        # Le chemin stocké est relatif à UPLOAD_FOLDER (ex: contact_attachments/fichier.pdf)
        directory = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
        
        # Sécurité : valider que le chemin est bien dans UPLOAD_FOLDER
        safe_filepath = secure_filename(message.attachment_filepath.replace("\\", "/"))
        full_path = os.path.abspath(os.path.join(directory, safe_filepath))
        if not full_path.startswith(directory):
             flash("Tentative d'accès à un fichier invalide.", "danger")
             current_app.logger.warning(f"Tentative de Path Traversal (message attachment): user {current_user.id}, path {safe_filepath}")
             return redirect(url_for('main.admin_messages_list'))
             
        return send_from_directory(
            directory, 
            safe_filepath, 
            as_attachment=True, # Forcer le téléchargement
            download_name=message.attachment_filename # Utiliser le nom original pour le téléchargement
        )
    else:
        flash("Ce message n'a pas de pièce jointe.", "warning")
        return redirect(url_for('main.admin_message_detail', message_id=message_id))

# ... (autres routes admin existantes) ...

@main_bp.route('/a-propos')
def about_us():
    return render_template('a_propos.html', title="À Propos d'Act4Community")