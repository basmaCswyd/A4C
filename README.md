# Plateforme de Gestion de Projets Act4Community

Bienvenue sur le dépôt de la Plateforme de Gestion de Projets Act4Community. Cette application web a été développée pour faciliter la soumission, l'évaluation et la gestion des projets communautaires.

## Table des Matières

- [À Propos du Projet](#à-propos-du-projet)
- [Fonctionnalités](#fonctionnalités)
- [Technologies Utilisées](#technologies-utilisées)
- [Prérequis](#prérequis)
- [Installation et Lancement](#installation-et-lancement)
  - [Configuration de la Base de Données](#configuration-de-la-base-de-données)
  - [Variables d'Environnement](#variables-denvironnement)
  - [Commandes Initiales](#commandes-initiales)
  - [Lancer l'Application](#lancer-lapplication)
- [Structure du Projet](#structure-du-projet)
- [Contribuer](#contribuer) <!-- Optionnel -->
- [Licence](#licence) <!-- Optionnel -->

## À Propos du Projet

Cette plateforme vise à numériser et optimiser le processus de gestion des initiatives pour Act4Community. Elle offre des interfaces distinctes pour les candidats, les membres évaluateurs d'Act4Community et les administrateurs du système.

## Fonctionnalités

### Pour les Candidats :
*   Inscription et connexion.
*   Soumission de nouveaux projets avec détails (description, budget, localisation, etc.) et documents joints.
*   Suivi du statut de leurs projets soumis (Soumis, En évaluation, Approuvé, Rejeté).
*   Téléchargement d'une convocation PDF si leur projet est approuvé et qu'un rendez-vous est fixé.

### Pour les Membres Act4Community (Évaluateurs) :
*   Inscription et connexion.
*   Consultation de la liste des projets en attente d'évaluation.
*   Évaluation détaillée des projets (notation, commentaires).
*   Consultation des statistiques de base.

### Pour les Administrateurs :
*   Toutes les fonctionnalités des membres évaluateurs.
*   Gestion des utilisateurs (voir, modifier rôles, supprimer).
*   Gestion des projets (approuver, rejeter les soumissions).
*   Définition des détails de rendez-vous pour les projets approuvés.
*   Tableau de bord avec des indicateurs clés.
*   Consultation des statistiques et rapports.

## Technologies Utilisées

*   **Backend :** Python avec le micro-framework Flask.
    *   **ORM :** Flask-SQLAlchemy
    *   **Authentification :** Flask-Login
    *   **Formulaires :** Flask-WTF
    *   **Génération PDF :** WeasyPrint
*   **Base de Données :** MySQL
*   **Frontend :** HTML5, CSS3 (sans framework CSS majeur comme Bootstrap), JavaScript (minimaliste pour l'interactivité).
*   **Gestion de l'environnement :** Pip avec `venv`.

## Prérequis

Avant de commencer, assurez-vous d'avoir installé :
*   Python 3.8+
*   Pip (généralement inclus avec Python)
*   Un serveur MySQL (par exemple, via XAMPP, WAMP, MAMP, ou une installation autonome)
*   phpMyAdmin (ou un autre outil de gestion MySQL) pour configurer la base de données.
*   Dépendances système pour WeasyPrint (GTK3 Runtime pour Windows). Consultez la [documentation WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) pour les détails spécifiques à votre OS.

## Installation et Lancement

1.  **Cloner le dépôt :**
    ```bash
    git clone https://github.com/VOTRE_NOM_UTILISATEUR/act4community_project.git
    cd act4community_project
    ```

2.  **Créer et activer un environnement virtuel :**
    ```bash
    python -m venv venv
    # Sur Windows:
    venv\Scripts\activate
    # Sur macOS/Linux:
    source venv/bin/activate
    ```

3.  **Installer les dépendances Python :**
    ```bash
    pip install -r requirements.txt 
    ```
    *(Note : Vous devrez créer un fichier `requirements.txt` en exécutant `pip freeze > requirements.txt` dans votre environnement virtuel activé une fois que tout fonctionne.)*
    Alternativement, si `requirements.txt` n'existe pas encore :
    ```bash
    pip install Flask Flask-SQLAlchemy Flask-Login Flask-WTF Werkzeug email-validator PyMySQL WeasyPrint
    ```

### Configuration de la Base de Données

1.  Assurez-vous que votre serveur MySQL est en cours d'exécution.
2.  Via phpMyAdmin (ou un outil similaire) :
    *   Créez une nouvelle base de données nommée `act4community_db` (avec interclassement `utf8mb4_unicode_ci`).
    *   Créez un utilisateur de base de données (par exemple, `act4_user`).
    *   Donnez à cet utilisateur tous les privilèges sur la base de données `act4community_db`. Notez bien le mot de passe de cet utilisateur.

### Variables d'Environnement

1.  Créez un fichier `config.py` à la racine du projet (à côté de `run.py`) s'il n'est pas déjà inclus et versionné (s'il contient des secrets, il ne devrait pas être versionné, utilisez plutôt un fichier `.env` et `python-dotenv`). Pour ce projet, nous l'avons inclus, mais **NE COMMETTEZ JAMAIS DE VRAIS SECRETS DANS UN DÉPÔT PUBLIC.**
2.  Modifiez `config.py` pour y mettre vos identifiants de base de données :
    ```python
    # Dans config.py
    # ...
    MYSQL_USER = 'act4_user' # Ou votre nom d'utilisateur DB
    MYSQL_PASSWORD = 'VOTRE_MOT_DE_PASSE_MYSQL_SECRET' # <--- METTEZ VOTRE VRAI MOT DE PASSE
    MYSQL_DB = 'act4community_db'
    # ...
    SECRET_KEY = 'votre_propre_cle_secrete_longue_et_aleatoire' # Changez ceci !
    ```

### Commandes Initiales

1.  Assurez-vous que votre environnement virtuel est activé.
2.  Définissez la variable d'application Flask :
    *   Windows CMD: `set FLASK_APP=act4community`
    *   Windows PowerShell: `$env:FLASK_APP="act4community"`
    *   macOS/Linux: `export FLASK_APP=act4community`
3.  Initialisez la base de données (crée les tables) :
    ```bash
    flask init-db
    ```
4.  Créez un compte administrateur pour l'application :
    ```bash
    flask create-admin
    ```
    Suivez les instructions pour définir le nom d'utilisateur, l'email et le mot de passe.

### Lancer l'Application

```bash
python run.py
