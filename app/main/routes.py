from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import EncryptedFile, FileShare, AuditLog

# Make sure the blueprint is defined correctly
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', title='Home')

@main.route('/dashboard')
@login_required
def dashboard():
    files = EncryptedFile.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', title='Dashboard', files=files)

@main.route('/shared')
@login_required
def shared_files():
    # Get files shared with the current user
    shared_files = EncryptedFile.query.join(EncryptedFile.shared_with).filter_by(shared_with_id=current_user.id).all()
    return render_template('shared_files.html', title='Shared Files', files=shared_files)

@main.route('/audit_logs')
@login_required
def audit_logs():
    # Only show logs for admin users or for the user's own files
    if current_user.username == 'admin':
        logs = AuditLog.query.all()
    else:
        logs = AuditLog.query.join(EncryptedFile).filter(EncryptedFile.user_id == current_user.id).all()
    
    return render_template('audit_logs.html', title='Audit Logs', logs=logs)