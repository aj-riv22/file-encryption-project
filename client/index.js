const path = require('path');
const fs = require('fs-extra');
const prompt = require('prompt-sync')({ sigint: true });
const crypto = require('crypto');
const axios = require('axios');
require('dotenv').config();

const { 
  generateEncryptionKey, 
  deriveKeyFromPassword,
  generateSalt,
  saveKey,
  loadKey
} = require('./encryption/crypto');

const SyncManager = require('./sync/sync_manager');

// Configuration
const CONFIG_DIR = path.join(process.env.HOME || process.env.USERPROFILE, '.encrip');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');
const KEY_FILE = path.join(CONFIG_DIR, 'key.dat');
const SERVER_URL = process.env.SERVER_URL || 'http://localhost:5000';

// Ensure config directory exists
fs.ensureDirSync(CONFIG_DIR);

/**
 * Main application entry point
 */
async function main() {
  console.log('Encrip Client - Secure File Synchronization');
  console.log('------------------------------------------');
  
  // Load or create configuration
  let config = await loadConfig();
  
  if (!config.username) {
    await registerOrLogin();
    config = await loadConfig(); // Reload config after login
  } else {
    console.log(`Logged in as: ${config.username}`);
    
    // Check if token is valid
    if (!(await isTokenValid(config.accessToken))) {
      console.log('Session expired, please login again.');
      await login();
      config = await loadConfig(); // Reload config after login
    }
  }
  
  // Get encryption key
  let encryptionKey = await getEncryptionKey();
  
  // Initialize sync manager
  const syncManager = new SyncManager({
    syncDir: path.join(process.cwd(), 'sync'),
    tempDir: path.join(CONFIG_DIR, 'temp'),
    serverUrl: SERVER_URL,
    accessToken: config.accessToken,
    encryptionKey: encryptionKey,
    autoSync: true
  });
  
  // Show menu
  await showMenu(syncManager);
}

/**
 * Load configuration from file
 */
async function loadConfig() {
  try {
    if (await fs.pathExists(CONFIG_FILE)) {
      const configData = await fs.readFile(CONFIG_FILE, 'utf8');
      return JSON.parse(configData);
    }
  } catch (error) {
    console.error('Error loading configuration:', error.message);
  }
  
  return {
    username: null,
    accessToken: null
  };
}

/**
 * Save configuration to file
 */
async function saveConfig(config) {
  try {
    await fs.writeFile(CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');
  } catch (error) {
    console.error('Error saving configuration:', error.message);
  }
}

/**
 * Register a new user or login
 */
async function registerOrLogin() {
  console.log('\n1. Register a new account');
  console.log('2. Login to existing account');
  
  const choice = prompt('Select an option (1-2): ');
  
  if (choice === '1') {
    await register();
  } else {
    await login();
  }
}

/**
 * Register a new user
 */
async function register() {
  console.log('\n=== Register a new account ===');
  
  const username = prompt('Username: ');
  const password = prompt('Password: ', { echo: '*' });
  
  try {
    const response = await axios.post(`${SERVER_URL}/api/auth/register`, {
      username,
      password
    });
    
    console.log('Registration successful!');
    
    // Save config
    await saveConfig({
      username,
      accessToken: response.data.access_token
    });
    
    // Generate and save encryption key
    const encryptionKey = generateEncryptionKey();
    await saveKey(encryptionKey, KEY_FILE, password);
    
    console.log('Encryption key generated and saved.');
    
  } catch (error) {
    console.error('Registration failed:', error.response?.data?.error || error.message);
  }
}

/**
 * Login to existing account
 */
async function login() {
  console.log('\n=== Login to your account ===');
  
  const username = prompt('Username: ');
  const password = prompt('Password: ', { echo: '*' });
  
  try {
    const response = await axios.post(`${SERVER_URL}/api/auth/login`, {
      username,
      password
    });
    
    console.log('Login successful!');
    
    // Save config
    await saveConfig({
      username,
      accessToken: response.data.access_token
    });
    
  } catch (error) {
    console.error('Login failed:', error.response?.data?.error || error.message);
  }
}

/**
 * Check if the access token is valid
 */
async function isTokenValid(token) {
  if (!token) return false;
  
  try {
    await axios.get(`${SERVER_URL}/api/auth/profile`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Get the encryption key
 */
async function getEncryptionKey() {
  try {
    if (await fs.pathExists(KEY_FILE)) {
      const config = await loadConfig();
      const password = prompt('Enter password to decrypt your key: ', { echo: '*' });
      
      return loadKey(KEY_FILE, password);
    } else {
      const config = await loadConfig();
      const password = prompt('Enter password to encrypt your new key: ', { echo: '*' });
      
      const encryptionKey = generateEncryptionKey();
      await saveKey(encryptionKey, KEY_FILE, password);
      
      console.log('New encryption key generated and saved.');
      return encryptionKey;
    }
  } catch (error) {
    console.error('Error getting encryption key:', error.message);
    process.exit(1);
  }
}

/**
 * Show main menu
 */
async function showMenu(syncManager) {
  console.log('\n=== Encrip Client ===');
  console.log('1. Initialize and start sync');
  console.log('2. Force sync now');
  console.log('3. Show sync status');
  console.log('4. Logout');
  console.log('5. Exit');
  
  const choice = prompt('Select an option (1-5): ');
  
  switch (choice) {
    case '1':
      await syncManager.initialize();
      break;
    case '2':
      await syncManager.syncWithServer();
      break;
    case '3':
      console.log('Sync directory:', syncManager.config.syncDir);
      console.log('Auto-sync:', syncManager.config.autoSync ? 'Enabled' : 'Disabled');
      break;
    case '4':
      await saveConfig({
        username: null,
        accessToken: null
      });
      console.log('Logged out successfully.');
      process.exit(0);
      break;
    case '5':
      console.log('Exiting Encrip client.');
      syncManager.stopWatching();
      process.exit(0);
      break;
    default:
      console.log('Invalid option.');
  }
  
  // Show menu again
  await showMenu(syncManager);
}

// Start the application
main().catch(error => {
  console.error('An error occurred:', error.message);
  process.exit(1);
}); 