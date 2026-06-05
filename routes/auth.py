from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_babel import gettext as _

import models.user as UserModel
from routes import establish_session, logout_session
from services.redirect_safety import safe_redirect_target

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration view (legacy credential account)."""
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        errors = []
        if not username or len(username) < 3:
            errors.append(_('Username must be at least 3 characters.'))
        if not email or '@' not in email:
            errors.append(_('Please enter a valid email address.'))
        if len(password) < 6:
            errors.append(_('Password must be at least 6 characters.'))
        if password != confirm:
            errors.append(_('Passwords do not match.'))
        if UserModel.username_exists(username):
            errors.append(_('That username is already taken.'))
        if UserModel.email_exists(email):
            errors.append(_('That email is already in use.'))

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html', username=username, email=email)

        UserModel.create_user(username, email, password)
        flash(_('Registration complete! Please sign in.'), 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Credential login view."""
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = UserModel.find_by_username(username)
        if user and UserModel.verify_password(user, password):
            establish_session(user, provider='local')
            flash(_('Welcome back, %(username)s!', username=user['username']), 'success')
            return redirect(safe_redirect_target(request.args.get('next')))
        flash(_('Incorrect username or password.'), 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Log out of all authentication methods (keeps selected language)."""
    logout_session()
    flash(_('You have been signed out.'), 'info')
    return redirect(url_for('main.index'))
