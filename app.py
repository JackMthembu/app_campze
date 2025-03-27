import os
from flask import Flask, current_app, jsonify, render_template, send_from_directory
from flask_login import login_required
from config import Config
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from datetime import timedelta, datetime
import time
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from dotenv import load_dotenv
from models import Currency, Country, State, User
from tour_operator import tour_operator
from app import db, login_manager, mail, migrate, celery

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Set application root path
    if os.environ.get('WEBSITE_HOSTNAME'):
        # Azure environment
        app.root_path = '/home/site/wwwroot'
        app.static_folder = '/home/site/wwwroot/static'
        app.template_folder = '/home/site/wwwroot/templates'
    else:
        # Local environment
        app.root_path = os.path.abspath(os.path.dirname(__file__))
        app.static_folder = 'static'
        app.template_folder = 'templates'
    
    # Security configurations
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ydjjKSDFDSJHhhdndvfasnjvdfNASAAOPOEFJCVBNdbsnsjKJSJFNDJJkkdjfnnfjdjkdkd')
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Database configurations
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30
    }
    
    # API and upload configurations
    app.config['GOOGLE_MAPS_API_KEY'] = os.getenv('GOOGLE_MAPS_API_KEY')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    # Set upload folder based on environment
    if os.environ.get('WEBSITE_HOSTNAME'):
        # Azure environment
        app.config['UPLOAD_FOLDER_PROFILE'] = '/home/site/wwwroot/static/uploads/profile'
    else:
        # Local environment
        app.config['UPLOAD_FOLDER_PROFILE'] = 'static/uploads/profile'

    # Ensure upload directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER_PROFILE']):
        os.makedirs(app.config['UPLOAD_FOLDER_PROFILE'])

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth_routes.login'

    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    csrf.init_app(app)
    WTF_CSRF_TIME_LIMIT = None

    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": ["https://campze.co", "https://campze.com"]}})
    
    # Initialize database with retry logic
    max_retries = 3
    retry_delay = 5  # seconds
    
    with app.app_context():
        for attempt in range(max_retries):
            try:
                db.engine.connect()
                break
            except OperationalError as e:
                if attempt == max_retries - 1:
                    app.logger.error(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
                    raise
                app.logger.warning(f"Database connection attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    # Add template context processor for global variables
    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.now()
        }
    
    # Set up database session handling
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            app.logger.error(f"Error during request: {str(exception)}")
            db.session.rollback()
        db.session.remove()

    # Add database error handler
    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        app.logger.error(f"Database error occurred: {str(error)}")
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except SQLAlchemyError as e:
            app.logger.error(f"Error loading user {user_id}: {str(e)}")
            return None

    # Import routes and models after extensions are initialized
    from auth import auth_routes
    from routes import main, allowed_file
    from profiles import profile_routes
    from booking import booking_routes
    from parent import parent_routes
    from organiser import organiser
    from errors import errors

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth_routes, url_prefix='/auth')
    app.register_blueprint(profile_routes, url_prefix='/profile')
    app.register_blueprint(booking_routes, url_prefix='/booking')
    app.register_blueprint(parent_routes, url_prefix='/parent')
    app.register_blueprint(organiser, url_prefix='/organiser')
    app.register_blueprint(errors)
    app.register_blueprint(tour_operator, url_prefix='/tour_operator')

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal server error: {str(error)}")
        return render_template('errors/500.html'), 500
    
    # Routes
    @app.route('/get_states/<country_id>', methods=['GET'])
    def get_states(country_id):
        try:
            country = Country.query.filter_by(id=country_id).first()
            if not country:
                return jsonify({'error': 'Country not found'}), 404
            states = State.query.filter_by(country_id=country.id).all()
            state_data = [{'id': state.id, 'name': state.state} for state in states]
            return jsonify(state_data)
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/get_currency/<country_id>')
    @login_required
    def get_currency(country_id):
        try:
            # Get country and join with currency
            currency = Currency.query.select_from(Country).join(Currency)\
                .filter(Country.id == country_id).first()
            
            if not currency:
                current_app.logger.error(f"No currency found for country: {country_id}")
                return jsonify({
                    'success': False,
                    'error': 'Currency not found'
                }), 404
            
            current_app.logger.debug(f"Found currency: {currency.id} for country: {country_id}")
            
            return jsonify({
                'success': True,
                'currency_id': currency.id
            })
            
        except Exception as e:
            current_app.logger.error(f"Error fetching currency for country {country_id}: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static/img'),
                                'favicon.png', mimetype='image/png')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=8000)
