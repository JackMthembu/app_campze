from flask import Blueprint, render_template

errors = Blueprint('errors', __name__)

@errors.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 Page Not Found errors"""
    return render_template('errors/404.html'), 404

@errors.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 Forbidden errors"""
    return render_template('errors/403.html'), 403

@errors.app_errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors"""
    return render_template('errors/500.html'), 500

@errors.app_errorhandler(400)
def bad_request_error(error):
    """Handle 400 Bad Request errors"""
    return render_template('errors/400.html'), 400

@errors.app_errorhandler(401)
def unauthorized_error(error):
    """Handle 401 Unauthorized errors"""
    return render_template('errors/401.html'), 401 