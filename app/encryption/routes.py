from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app.models import EncryptedFile, AuditLog, FileShare, User
from app.encryption.forms import EncryptForm, DecryptForm, ShareFileForm
from app.utils.crypto import encrypt_file_aes, decrypt_file_aes
import uuid
from app import db

# Define the blueprint
encryption = Blueprint('encryption', __name__)

def allowed_file(filename):
    # Allow all file types for encryption
    return True

@encryption.route('/encrypt', methods=['GET', 'POST'])
@login_required
def encrypt():
    form = EncryptForm()
    if form.validate_on_submit():
        file = form.file.data
        if file and allowed_file(file.filename):
            # Secure the filename
            original_filename = secure_filename(file.filename)
            
            # Generate unique filename for the encrypted file
            encrypted_filename = f"{uuid.uuid4().hex}.enc"
            
            # Save the original file temporarily
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_' + original_filename)
            file.save(temp_path)
            
            # Encrypt the file
            encrypted_path = os.path.join(current_app.config['UPLOAD_FOLDER'], encrypted_filename)
            salt, file_hash = encrypt_file_aes(temp_path, encrypted_path, form.password.data)
            
            # Remove the temporary file
            os.remove(temp_path)
            
            # Save file information to database
            new_file = EncryptedFile(
                encrypted_filename=encrypted_filename,  # Use encrypted_filename instead of filename
                original_filename=original_filename,
                encryption_method='AES-256',
                file_hash=file_hash,
                user_id=current_user.id
            )
            db.session.add(new_file)
            
            # Log the action
            log = AuditLog(
                user_id=current_user.id,
                file_id=new_file.id,
                action='encrypt',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('File encrypted successfully!')
            return redirect(url_for('main.dashboard'))
    
    return render_template('encryption/encrypt.html', title='Encrypt File', form=form)

@encryption.route('/decrypt/<int:file_id>', methods=['GET', 'POST'])
@login_required
def decrypt(file_id):
    file = EncryptedFile.query.get_or_404(file_id)
    
    # Check if user has permission to decrypt this file
    if file.user_id != current_user.id and not FileShare.query.filter_by(
            file_id=file.id, shared_with_id=current_user.id).first():
        flash('You do not have permission to decrypt this file.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = DecryptForm()
    if form.validate_on_submit():
        # Get the encrypted file path
        encrypted_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.encrypted_filename)
        
        # Generate path for decrypted file
        decrypted_filename = f"decrypted_{file.original_filename}"
        decrypted_path = os.path.join(current_app.config['UPLOAD_FOLDER'], decrypted_filename)
        
        # Decrypt the file
        success, message = decrypt_file_aes(encrypted_path, decrypted_path, form.password.data)
        
        if success:
            # Log the decryption
            log = AuditLog(
                user_id=current_user.id,
                file_id=file.id,
                action="Decrypted file",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('File decrypted successfully!', 'success')
            return send_file(decrypted_path, as_attachment=True, download_name=file.original_filename)
        else:
            flash(message, 'danger')
            return redirect(url_for('encryption.decrypt', file_id=file.id))
    
    return render_template('encryption/decrypt.html', title='Decrypt File', form=form, file=file)

@encryption.route('/share/<int:file_id>', methods=['GET', 'POST'])
@login_required
def share_file(file_id):
    file = EncryptedFile.query.get_or_404(file_id)
    
    # Check if user has permission to share this file
    if file.user_id != current_user.id:
        flash('You do not have permission to share this file.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = ShareFileForm()
    # Populate user choices with all users except current user
    form.user.choices = [(u.id, u.username) for u in User.query.filter(User.id != current_user.id).all()]
    
    if form.validate_on_submit():
        # Check if file is already shared with this user
        if FileShare.query.filter_by(file_id=file.id, shared_with_id=form.user.data).first():
            flash('File is already shared with this user.', 'warning')
            return redirect(url_for('main.dashboard'))
        
        # Create new file share
        share = FileShare(
            file_id=file.id,
            shared_with_id=form.user.data,
            access_level=form.access_level.data
        )
        db.session.add(share)
        db.session.commit()
        
        # Generate a share link - make sure this matches your route definition
        share_link = url_for('encryption.access_shared', share_id=share.id, _external=True)
        
        # Log the share action
        log = AuditLog(
            user_id=current_user.id,
            file_id=file.id,
            action=f"Shared with user ID {form.user.data}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'File shared successfully! Share link: {share_link}', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('encryption/share.html', title='Share File', form=form, file=file)

# Remove this line and its decorator
# @encryption.route('/shared/<share_link>')
# @login_required
# Keep only this route:
@encryption.route('/access_shared/<int:share_id>', methods=['GET'])
@login_required
def access_shared(share_id):
    # Get the file share
    share = FileShare.query.get_or_404(share_id)
    
    # Check if current user is the one the file is shared with
    if share.shared_with_id != current_user.id:
        flash('You do not have permission to access this shared file.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get the file
    file = EncryptedFile.query.get_or_404(share.file_id)
    
    # Log the access
    log = AuditLog(
        user_id=current_user.id,
        file_id=file.id,
        action="Accessed shared file",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return render_template('encryption/shared_file.html', title='Shared File', file=file, share=share)