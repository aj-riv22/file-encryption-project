import os
import requests
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from pathlib import Path

class CloudClient:
    def __init__(self, server_url, username, password):
        self.server_url = server_url
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.sync_path = None

    def authenticate(self):
        response = requests.post(
            f"{self.server_url}/api/token/",
            data={
                "username": self.username,
                "password": self.password
            }
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access"]
            self.refresh_token = data["refresh"]
            return True
        return False

    def refresh_auth_token(self):
        response = requests.post(
            f"{self.server_url}/api/token/refresh/",
            data={"refresh": self.refresh_token}
        )
        if response.status_code == 200:
            self.access_token = response.json()["access"]
            return True
        return False

    def upload_file(self, file_path, encrypt=False):
        relative_path = os.path.relpath(file_path, self.sync_path)
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'path': relative_path, 'encrypt': encrypt}
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            response = requests.post(
                f"{self.server_url}/api/files/",
                files=files,
                data=data,
                headers=headers
            )
            return response.status_code == 201

    def download_file(self, file_id):
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = requests.get(
            f"{self.server_url}/api/files/{file_id}/download/",
            headers=headers,
            stream=True
        )
        
        if response.status_code == 200:
            return response.content
        return None

    def start_sync(self, sync_path):
        self.sync_path = sync_path
        sync_service = SyncService(self, sync_path)
        sync_service.start()

class ClientFileEventHandler(FileSystemEventHandler):
    def __init__(self, client):
        self.client = client
        self.last_modified = {}

    def on_modified(self, event):
        if event.is_directory:
            return
            
        current_time = time.time()
        if (event.src_path in self.last_modified and 
            current_time - self.last_modified[event.src_path] < 1):
            return
            
        self.last_modified[event.src_path] = current_time
        self.client.upload_file(event.src_path)

class SyncService:
    def __init__(self, client, watch_path):
        self.client = client
        self.watch_path = watch_path
        self.handler = ClientFileEventHandler(client)
        self.observer = Observer()

    def start(self):
        self.observer.schedule(self.handler, self.watch_path, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()
