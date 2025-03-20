from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_required
from forms import ProfileForm, ProfilePicForm
from models import Banks, Country, User, Currency, BankingDetails, Guardian, Child
from extensions import db
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload

import os

from routes import allowed_file


profile_routes = Blueprint('profile_routes', __name__)

