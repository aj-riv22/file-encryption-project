import os
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from models.file import File

files_bp = Blueprint('files', __name__, url_prefix='/api/files')

def allowed_file(filename):
    # Allow all files - encryption is handled client-side
    return True

@files_bp.route('', methods=['GET'])
@jwt_required()
def list_files():
    current_user = get_jwt_identity()
    
    # Get all files for the current user
    files = File.find_by_owner(current_user)
    
    # Convert to list of dictionaries for JSON response
    files_list = [file.to_dict() for file in files]
    
    return jsonify({"files": files_list}), 200

@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user = get_jwt_identity()
    
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser submits an empty part without filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Generate a unique filename for storage
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{current_user}_{filename}")
        
        # Save the file to disk
        file.save(file_path)
        
        # Create metadata in database
        file_obj = File(
            name=filename,
            path=file_path,
            owner=current_user,
            size=os.path.getsize(file_path),
            content_type=file.content_type
        )
        file_obj.save()
        
        return jsonify({
            "message": "File uploaded successfully",
            "file": file_obj.to_dict()
        }), 201
    
    return jsonify({"error": "File type not allowed"}), 400

@files_bp.route('/<file_id>', methods=['GET'])
@jwt_required()
def download_file(file_id):
    current_user = get_jwt_identity()
    
    # Get file from database
    file_obj = File.find_by_id(file_id)
    
    if not file_obj:
        return jsonify({"error": "File not found"}), 404
    
    # Check if user has access to this file
    if file_obj.owner != current_user:
        return jsonify({"error": "Unauthorized access"}), 403
    
    # Send the file
    return send_file(file_obj.path, download_name=file_obj.name)

@files_bp.route('/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    current_user = get_jwt_identity()
    
    # Get file from database
    file_obj = File.find_by_id(file_id)
    
    if not file_obj:
        return jsonify({"error": "File not found"}), 404
    
    # Check if user has access to this file
    if file_obj.owner != current_user:
        return jsonify({"error": "Unauthorized access"}), 403
    
    # Delete file from disk
    try:
        os.remove(file_obj.path)
    except OSError:
        pass  # File might not exist on disk
    
    # Delete file from database
    file_obj.delete()
    
    return jsonify({"message": "File deleted successfully"}), 200 