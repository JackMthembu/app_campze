from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

main = Blueprint('main', __name__)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.context_processor
def inject_now():
    """Add current year to template context"""
    return {'now': datetime.utcnow()}

@main.route('/')
def index():
    """Main landing page with role-based redirection for authenticated users"""
    if current_user.is_authenticated:
        if current_user.role == 'organiser':
            return redirect(url_for('organiser.dashboard'))
        elif current_user.role == 'parent':
            return redirect(url_for('parent.dashboard'))
        elif current_user.role == 'child':
            return redirect(url_for('child.dashboard'))
        else:
            return redirect(url_for('auth_routes.login'))
    return render_template('landing.html')

@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page for authenticated users"""
    if current_user.role == 'organiser':
        return redirect(url_for('organiser.dashboard'))
    elif current_user.role == 'parent':
        return redirect(url_for('parent.dashboard'))
    elif current_user.role == 'child':
        return redirect(url_for('child.dashboard'))
    return render_template('dashboard/dashboard.html')

@main.route('/change_password')
@login_required
def change_password():
    return render_template('dashboard/change_password.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('dashboard/profile.html')

@main.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main.route('/terms')
def terms():
    return render_template('terms.html')





