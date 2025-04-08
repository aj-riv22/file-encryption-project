from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    files = db.relationship('EncryptedFile', backref='owner', lazy='dynamic')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class EncryptedFile(db.Model):
    __tablename__ = 'encrypted_files'
    
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255))
    encrypted_filename = db.Column(db.String(255), unique=True)
    encryption_method = db.Column(db.String(50), default='AES-256')
    file_hash = db.Column(db.String(64))  # For integrity verification
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    shared_with = db.relationship('FileShare', backref='file', lazy='dynamic')
    
    def __repr__(self):
        return f'<EncryptedFile {self.original_filename}>'

class FileShare(db.Model):
    __tablename__ = 'file_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('encrypted_files.id'))
    shared_with_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    access_level = db.Column(db.String(20), default='read')  # read, edit, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to the user the file is shared with
    shared_user = db.relationship('User', backref='shared_files')
    
    def __repr__(self):
        return f'<FileShare {self.file_id} with {self.shared_with_id}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    file_id = db.Column(db.Integer, db.ForeignKey('encrypted_files.id'))
    action = db.Column(db.String(50))  # encrypt, decrypt, share, access_shared
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    file = db.relationship('EncryptedFile', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id} on {self.file_id}>'