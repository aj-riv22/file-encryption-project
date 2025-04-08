import uuid
from datetime import datetime
from storage.db import get_db

class User:
    def __init__(self, username, password, user_id=None, created_at=None):
        self.user_id = user_id or str(uuid.uuid4())
        self.username = username
        self.password = password
        self.created_at = created_at or datetime.utcnow()
    
    def save(self):
        db = get_db()
        users = db.users
        
        user_data = {
            "user_id": self.user_id,
            "username": self.username,
            "password": self.password,
            "created_at": self.created_at
        }
        
        if users.find_one({"user_id": self.user_id}):
            users.update_one({"user_id": self.user_id}, {"$set": user_data})
        else:
            users.insert_one(user_data)
    
    @staticmethod
    def find_by_username(username):
        db = get_db()
        user_data = db.users.find_one({"username": username})
        
        if user_data:
            return User(
                username=user_data["username"],
                password=user_data["password"],
                user_id=user_data["user_id"],
                created_at=user_data["created_at"]
            )
        
        return None
    
    @staticmethod
    def find_by_id(user_id):
        db = get_db()
        user_data = db.users.find_one({"user_id": user_id})
        
        if user_data:
            return User(
                username=user_data["username"],
                password=user_data["password"],
                user_id=user_data["user_id"],
                created_at=user_data["created_at"]
            )
        
        return None 