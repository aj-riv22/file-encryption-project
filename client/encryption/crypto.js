const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

/**
 * Generate a random encryption key
 * @param {number} byteLength - Length of the key in bytes (default: 32 for AES-256)
 * @returns {Buffer} Random key
 */
function generateEncryptionKey(byteLength = 32) {
  return crypto.randomBytes(byteLength);
}

/**
 * Derive an encryption key from a password
 * @param {string} password - User password
 * @param {Buffer} salt - Salt for key derivation
 * @returns {Buffer} Derived key
 */
function deriveKeyFromPassword(password, salt) {
  // Use PBKDF2 for key derivation with 100,000 iterations
  return crypto.pbkdf2Sync(password, salt, 100000, 32, 'sha256');
}

/**
 * Generate a random salt for key derivation
 * @param {number} byteLength - Length of the salt in bytes
 * @returns {Buffer} Random salt
 */
function generateSalt(byteLength = 16) {
  return crypto.randomBytes(byteLength);
}

/**
 * Encrypt a file with the provided key
 * @param {string} inputPath - Path to the input file
 * @param {string} outputPath - Path to the output encrypted file
 * @param {Buffer} key - Encryption key
 * @returns {Object} Metadata about the encrypted file
 */
function encryptFile(inputPath, outputPath, key) {
  // Generate a random IV
  const iv = crypto.randomBytes(16);
  
  // Create Cipher
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
  
  // Read input file
  const inputData = fs.readFileSync(inputPath);
  
  // Encrypt the data
  let encryptedData = cipher.update(inputData);
  encryptedData = Buffer.concat([encryptedData, cipher.final()]);
  
  // Get the authentication tag
  const authTag = cipher.getAuthTag();
  
  // Write IV, authTag, and encrypted data to output file
  const outputData = Buffer.concat([
    iv,                    // 16 bytes
    authTag,               // 16 bytes
    encryptedData          // rest of the file
  ]);
  
  fs.writeFileSync(outputPath, outputData);
  
  return {
    originalSize: inputData.length,
    encryptedSize: outputData.length,
    iv: iv.toString('hex'),
    authTag: authTag.toString('hex'),
    algorithm: 'aes-256-gcm'
  };
}

/**
 * Decrypt a file with the provided key
 * @param {string} inputPath - Path to the encrypted input file
 * @param {string} outputPath - Path to the output decrypted file
 * @param {Buffer} key - Encryption key
 * @returns {boolean} Success status
 */
function decryptFile(inputPath, outputPath, key) {
  try {
    // Read the encrypted file
    const inputData = fs.readFileSync(inputPath);
    
    // Extract IV, authTag, and encryptedData
    const iv = inputData.slice(0, 16);
    const authTag = inputData.slice(16, 32);
    const encryptedData = inputData.slice(32);
    
    // Create Decipher
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
    decipher.setAuthTag(authTag);
    
    // Decrypt the data
    let decryptedData = decipher.update(encryptedData);
    decryptedData = Buffer.concat([decryptedData, decipher.final()]);
    
    // Write decrypted data to output file
    fs.writeFileSync(outputPath, decryptedData);
    
    return true;
  } catch (error) {
    console.error('Error decrypting file:', error.message);
    return false;
  }
}

/**
 * Save encryption key to a file, optionally protected with a password
 * @param {Buffer} key - Encryption key to save
 * @param {string} keyPath - Path to save the key file
 * @param {string} password - Optional password to protect the key file
 */
function saveKey(key, keyPath, password = null) {
  if (!password) {
    // Save the key directly if no password is provided
    fs.writeFileSync(keyPath, key);
    return;
  }
  
  // Generate a salt for key derivation
  const salt = generateSalt();
  
  // Derive a key from the password
  const derivedKey = deriveKeyFromPassword(password, salt);
  
  // Encrypt the master key using the derived key
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-gcm', derivedKey, iv);
  
  let encryptedKey = cipher.update(key);
  encryptedKey = Buffer.concat([encryptedKey, cipher.final()]);
  
  const authTag = cipher.getAuthTag();
  
  // Save the salt, IV, authTag, and encrypted key
  const keyFileData = Buffer.concat([
    salt,            // 16 bytes
    iv,              // 16 bytes
    authTag,         // 16 bytes
    encryptedKey     // 32 bytes (encrypted)
  ]);
  
  fs.writeFileSync(keyPath, keyFileData);
}

/**
 * Load an encryption key from a file, optionally decrypting it with a password
 * @param {string} keyPath - Path to the key file
 * @param {string} password - Optional password to decrypt the key file
 * @returns {Buffer} The encryption key
 */
function loadKey(keyPath, password = null) {
  const keyFileData = fs.readFileSync(keyPath);
  
  if (!password) {
    // Return the key directly if no password is provided
    return keyFileData;
  }
  
  // Extract salt, IV, authTag, and encrypted key
  const salt = keyFileData.slice(0, 16);
  const iv = keyFileData.slice(16, 32);
  const authTag = keyFileData.slice(32, 48);
  const encryptedKey = keyFileData.slice(48);
  
  // Derive the key from the password
  const derivedKey = deriveKeyFromPassword(password, salt);
  
  // Decrypt the master key
  const decipher = crypto.createDecipheriv('aes-256-gcm', derivedKey, iv);
  decipher.setAuthTag(authTag);
  
  let decryptedKey = decipher.update(encryptedKey);
  decryptedKey = Buffer.concat([decryptedKey, decipher.final()]);
  
  return decryptedKey;
}

module.exports = {
  generateEncryptionKey,
  deriveKeyFromPassword,
  generateSalt,
  encryptFile,
  decryptFile,
  saveKey,
  loadKey
}; 