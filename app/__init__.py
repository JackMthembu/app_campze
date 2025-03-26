from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_cors import CORS
from celery import Celery
from .config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
celery = Celery()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Configure Celery
    celery.conf.update(app.config)
    
    # Register blueprints
    from .routes import main, auth, admin, tour_operator, school
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(tour_operator.bp)
    app.register_blueprint(school.bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app 