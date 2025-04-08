import os
from pymongo import MongoClient
from flask import g, current_app

def get_db():
    """Get a MongoDB database connection"""
    if 'db' not in g:
        # Get MongoDB connection string from environment or use a default for local development
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
        client = MongoClient(mongo_uri)
        g.db = client.encrip_db
    
    return g.db

def close_db(e=None):
    """Close the MongoDB connection"""
    db = g.pop('db', None)
    
    if db is not None:
        db.client.close()

def init_app(app):
    """Register database functions with the Flask app"""
    app.teardown_appcontext(close_db) 