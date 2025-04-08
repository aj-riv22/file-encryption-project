import uuid
from datetime import datetime
from storage.db import get_db

class File:
    def __init__(self, name, path, owner, size, content_type, file_id=None, created_at=None, updated_at=None):
        self.file_id = file_id or str(uuid.uuid4())
        self.name = name
        self.path = path
        self.owner = owner
        self.size = size
        self.content_type = content_type
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def save(self):
        db = get_db()
        files = db.files
        
        file_data = {
            "file_id": self.file_id,
            "name": self.name,
            "path": self.path,
            "owner": self.owner,
            "size": self.size,
            "content_type": self.content_type,
            "created_at": self.created_at,
            "updated_at": datetime.utcnow()
        }
        
        if files.find_one({"file_id": self.file_id}):
            files.update_one({"file_id": self.file_id}, {"$set": file_data})
        else:
            files.insert_one(file_data)
    
    def delete(self):
        db = get_db()
        db.files.delete_one({"file_id": self.file_id})
    
    def to_dict(self):
        return {
            "file_id": self.file_id,
            "name": self.name,
            "size": self.size,
            "content_type": self.content_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @staticmethod
    def find_by_id(file_id):
        db = get_db()
        file_data = db.files.find_one({"file_id": file_id})
        
        if file_data:
            return File(
                name=file_data["name"],
                path=file_data["path"],
                owner=file_data["owner"],
                size=file_data["size"],
                content_type=file_data["content_type"],
                file_id=file_data["file_id"],
                created_at=file_data["created_at"],
                updated_at=file_data["updated_at"]
            )
        
        return None
    
    @staticmethod
    def find_by_owner(owner):
        db = get_db()
        files_data = db.files.find({"owner": owner})
        
        return [
            File(
                name=file_data["name"],
                path=file_data["path"],
                owner=file_data["owner"],
                size=file_data["size"],
                content_type=file_data["content_type"],
                file_id=file_data["file_id"],
                created_at=file_data["created_at"],
                updated_at=file_data["updated_at"]
            )
            for file_data in files_data
        ] 