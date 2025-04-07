from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from django.conf import settings
import os
import time
import threading

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, sync_service):
        self.sync_service = sync_service
        self.last_modified = {}

    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Debounce multiple events for the same file
        current_time = time.time()
        if (event.src_path in self.last_modified and 
            current_time - self.last_modified[event.src_path] < 1):
            return
            
        self.last_modified[event.src_path] = current_time
        self.sync_service.sync_file(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self.sync_service.upload_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.sync_service.delete_file(event.src_path)

class SyncService:
    def __init__(self, user, watch_path):
        self.user = user
        self.watch_path = watch_path
        self.handler = FileEventHandler(self)
        self.observer = Observer()
        self.file_handler = FileHandler(user)

    def start(self):
        self.observer.schedule(self.handler, self.watch_path, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def sync_file(self, file_path):
        relative_path = os.path.relpath(file_path, self.watch_path)
        with open(file_path, 'rb') as f:
            self.file_handler.save_file(f, relative_path)

    def upload_file(self, file_path):
        self.sync_file(file_path)

    def delete_file(self, file_path):
        relative_path = os.path.relpath(file_path, self.watch_path)
        File.objects.filter(
            owner=self.user,
            path=relative_path
        ).delete()
