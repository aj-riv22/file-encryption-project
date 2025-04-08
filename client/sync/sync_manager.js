const fs = require('fs-extra');
const path = require('path');
const crypto = require('crypto');
const watch = require('node-watch');
const axios = require('axios');
const { encryptFile, decryptFile } = require('../encryption/crypto');

class SyncManager {
  constructor(options) {
    this.config = {
      syncDir: options.syncDir || path.join(process.cwd(), 'sync'),
      tempDir: options.tempDir || path.join(process.cwd(), 'temp'),
      serverUrl: options.serverUrl || 'http://localhost:5000',
      accessToken: options.accessToken,
      encryptionKey: options.encryptionKey,
      autoSync: options.autoSync !== undefined ? options.autoSync : true
    };
    
    this.watcher = null;
    this.syncQueue = [];
    this.processing = false;
    this.fileMetadata = new Map();  // Maps local file paths to server file IDs
  }
  
  /**
   * Initialize the sync directory and start watching for changes
   */
  async initialize() {
    // Create directories if they don't exist
    await fs.ensureDir(this.config.syncDir);
    await fs.ensureDir(this.config.tempDir);
    
    // Load metadata if it exists
    await this._loadMetadata();
    
    // Start watching for changes if autoSync is enabled
    if (this.config.autoSync) {
      this._startWatching();
    }
    
    // Initial sync with server
    await this.syncWithServer();
  }
  
  /**
   * Start watching for file changes
   */
  _startWatching() {
    if (this.watcher) {
      this.watcher.close();
    }
    
    this.watcher = watch(this.config.syncDir, { recursive: true }, (evt, name) => {
      const relativePath = path.relative(this.config.syncDir, name);
      
      if (evt === 'update') {
        this._queueFileForUpload(relativePath);
      } else if (evt === 'remove') {
        this._queueFileForDeletion(relativePath);
      }
    });
    
    console.log(`Watching for changes in ${this.config.syncDir}`);
  }
  
  /**
   * Stop watching for file changes
   */
  stopWatching() {
    if (this.watcher) {
      this.watcher.close();
      this.watcher = null;
      console.log('Stopped watching for changes');
    }
  }
  
  /**
   * Queue a file for upload to the server
   */
  _queueFileForUpload(relativePath) {
    const localPath = path.join(this.config.syncDir, relativePath);
    
    // Skip directories and hidden files
    if (fs.statSync(localPath).isDirectory() || path.basename(localPath).startsWith('.')) {
      return;
    }
    
    this.syncQueue.push({
      action: 'upload',
      path: relativePath
    });
    
    this._processSyncQueue();
  }
  
  /**
   * Queue a file for deletion on the server
   */
  _queueFileForDeletion(relativePath) {
    // Check if we have metadata for this file
    if (this.fileMetadata.has(relativePath)) {
      this.syncQueue.push({
        action: 'delete',
        path: relativePath,
        fileId: this.fileMetadata.get(relativePath).fileId
      });
      
      this._processSyncQueue();
    }
  }
  
  /**
   * Process the sync queue
   */
  async _processSyncQueue() {
    if (this.processing || this.syncQueue.length === 0) {
      return;
    }
    
    this.processing = true;
    
    try {
      while (this.syncQueue.length > 0) {
        const syncItem = this.syncQueue.shift();
        
        if (syncItem.action === 'upload') {
          await this._uploadFile(syncItem.path);
        } else if (syncItem.action === 'delete') {
          await this._deleteFile(syncItem.path, syncItem.fileId);
        } else if (syncItem.action === 'download') {
          await this._downloadFile(syncItem.fileId, syncItem.path);
        }
      }
    } catch (error) {
      console.error('Error processing sync queue:', error.message);
    } finally {
      this.processing = false;
    }
  }
  
  /**
   * Upload a file to the server
   */
  async _uploadFile(relativePath) {
    const localPath = path.join(this.config.syncDir, relativePath);
    
    try {
      console.log(`Uploading ${relativePath}...`);
      
      // Create a temporary encrypted file
      const tempPath = path.join(this.config.tempDir, crypto.randomBytes(16).toString('hex'));
      
      // Encrypt the file
      await encryptFile(localPath, tempPath, this.config.encryptionKey);
      
      // Create form data
      const formData = new FormData();
      formData.append('file', fs.createReadStream(tempPath), { filename: path.basename(relativePath) });
      
      // Upload to server
      const response = await axios.post(`${this.config.serverUrl}/api/files/upload`, formData, {
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      // Clean up temporary file
      await fs.remove(tempPath);
      
      // Update metadata
      this.fileMetadata.set(relativePath, {
        fileId: response.data.file.file_id,
        name: response.data.file.name,
        modifiedAt: new Date()
      });
      
      await this._saveMetadata();
      
      console.log(`Upload complete: ${relativePath}`);
    } catch (error) {
      console.error(`Error uploading ${relativePath}:`, error.message);
    }
  }
  
  /**
   * Download a file from the server
   */
  async _downloadFile(fileId, destinationPath) {
    const localPath = path.join(this.config.syncDir, destinationPath);
    
    try {
      console.log(`Downloading ${destinationPath}...`);
      
      // Create a temporary file
      const tempPath = path.join(this.config.tempDir, crypto.randomBytes(16).toString('hex'));
      
      // Create directory if it doesn't exist
      await fs.ensureDir(path.dirname(localPath));
      
      // Download encrypted file
      const response = await axios.get(`${this.config.serverUrl}/api/files/${fileId}`, {
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`
        },
        responseType: 'arraybuffer'
      });
      
      // Save encrypted file to temporary location
      await fs.writeFile(tempPath, Buffer.from(response.data));
      
      // Decrypt the file
      await decryptFile(tempPath, localPath, this.config.encryptionKey);
      
      // Clean up temporary file
      await fs.remove(tempPath);
      
      console.log(`Download complete: ${destinationPath}`);
    } catch (error) {
      console.error(`Error downloading ${destinationPath}:`, error.message);
    }
  }
  
  /**
   * Delete a file from the server
   */
  async _deleteFile(relativePath, fileId) {
    try {
      console.log(`Deleting ${relativePath} from server...`);
      
      await axios.delete(`${this.config.serverUrl}/api/files/${fileId}`, {
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`
        }
      });
      
      // Remove from metadata
      this.fileMetadata.delete(relativePath);
      await this._saveMetadata();
      
      console.log(`Deletion complete: ${relativePath}`);
    } catch (error) {
      console.error(`Error deleting ${relativePath}:`, error.message);
    }
  }
  
  /**
   * Synchronize with the server
   */
  async syncWithServer() {
    try {
      console.log('Syncing with server...');
      
      // Get list of files from server
      const response = await axios.get(`${this.config.serverUrl}/api/files`, {
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`
        }
      });
      
      const serverFiles = response.data.files;
      
      // Get list of local files
      const localFiles = await this._getLocalFiles();
      
      // Compare and sync
      await this._reconcileFiles(localFiles, serverFiles);
      
      console.log('Sync with server complete');
    } catch (error) {
      console.error('Error syncing with server:', error.message);
    }
  }
  
  /**
   * Get list of all files in the sync directory
   */
  async _getLocalFiles() {
    const files = [];
    
    const walkDir = async (dir) => {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        const relativePath = path.relative(this.config.syncDir, fullPath);
        
        // Skip hidden files and directories
        if (entry.name.startsWith('.')) continue;
        
        if (entry.isDirectory()) {
          await walkDir(fullPath);
        } else {
          const stats = await fs.stat(fullPath);
          files.push({
            path: relativePath,
            modifiedAt: stats.mtime
          });
        }
      }
    };
    
    await walkDir(this.config.syncDir);
    return files;
  }
  
  /**
   * Reconcile differences between local and server files
   */
  async _reconcileFiles(localFiles, serverFiles) {
    // Create a map of server files by name for easier lookup
    const serverFileMap = new Map();
    for (const file of serverFiles) {
      serverFileMap.set(file.name, file);
    }
    
    // Check for files to download or update
    for (const serverFile of serverFiles) {
      const matchingLocalFile = localFiles.find(local => path.basename(local.path) === serverFile.name);
      
      if (!matchingLocalFile) {
        // File exists on server but not locally, download it
        this.syncQueue.push({
          action: 'download',
          fileId: serverFile.file_id,
          path: serverFile.name
        });
        
        // Update metadata
        this.fileMetadata.set(serverFile.name, {
          fileId: serverFile.file_id,
          name: serverFile.name,
          modifiedAt: new Date(serverFile.updated_at)
        });
      } else {
        // File exists both locally and on server
        const localModified = new Date(matchingLocalFile.modifiedAt);
        const serverModified = new Date(serverFile.updated_at);
        
        // Update metadata
        this.fileMetadata.set(matchingLocalFile.path, {
          fileId: serverFile.file_id,
          name: serverFile.name,
          modifiedAt: serverModified
        });
        
        // Only download if server version is newer
        if (serverModified > localModified) {
          this.syncQueue.push({
            action: 'download',
            fileId: serverFile.file_id,
            path: matchingLocalFile.path
          });
        }
      }
    }
    
    // Check for files to upload
    for (const localFile of localFiles) {
      const fileName = path.basename(localFile.path);
      
      if (!serverFileMap.has(fileName) && !this.fileMetadata.has(localFile.path)) {
        // File exists locally but not on server, upload it
        this.syncQueue.push({
          action: 'upload',
          path: localFile.path
        });
      }
    }
    
    await this._saveMetadata();
    this._processSyncQueue();
  }
  
  /**
   * Save metadata to disk
   */
  async _saveMetadata() {
    const metadataPath = path.join(this.config.syncDir, '.metadata.json');
    const metadataObj = {};
    
    for (const [path, data] of this.fileMetadata.entries()) {
      metadataObj[path] = data;
    }
    
    await fs.writeFile(metadataPath, JSON.stringify(metadataObj, null, 2), 'utf8');
  }
  
  /**
   * Load metadata from disk
   */
  async _loadMetadata() {
    const metadataPath = path.join(this.config.syncDir, '.metadata.json');
    
    try {
      if (await fs.pathExists(metadataPath)) {
        const metadataContent = await fs.readFile(metadataPath, 'utf8');
        const metadataObj = JSON.parse(metadataContent);
        
        this.fileMetadata.clear();
        for (const [path, data] of Object.entries(metadataObj)) {
          this.fileMetadata.set(path, data);
        }
        
        console.log('Loaded metadata for', this.fileMetadata.size, 'files');
      }
    } catch (error) {
      console.error('Error loading metadata:', error.message);
    }
  }
}

module.exports = SyncManager; 