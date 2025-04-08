from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key
import os
import hashlib

def generate_file_hash(file_path):
    """Generate SHA-256 hash of file for integrity verification"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def derive_key(password, salt=None):
    """Derive encryption key from password using PBKDF2"""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32 bytes = 256 bits for AES-256
        salt=salt,
        iterations=100000,
    )
    
    key = kdf.derive(password.encode())
    return key, salt

def encrypt_file_aes(input_path, output_path, password):
    """Encrypt a file using AES-256 with password-based key derivation"""
    # Generate key from password
    key, salt = derive_key(password)
    
    # Generate random IV
    iv = os.urandom(16)
    
    # Calculate file hash for integrity verification
    file_hash = generate_file_hash(input_path)
    
    # Create cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    
    # Create padder
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    
    with open(input_path, 'rb') as infile, open(output_path, 'wb') as outfile:
        # Write salt and IV to the beginning of the file
        outfile.write(salt)
        outfile.write(iv)
        
        # Write file hash for integrity verification
        outfile.write(file_hash.encode())
        
        # Encrypt and write data
        while True:
            chunk = infile.read(64 * 1024)  # 64KB chunks
            if not chunk:
                break
            
            padded_chunk = padder.update(chunk)
            encrypted_chunk = encryptor.update(padded_chunk)
            outfile.write(encrypted_chunk)
        
        # Finalize encryption
        padded_chunk = padder.finalize()
        encrypted_chunk = encryptor.update(padded_chunk) + encryptor.finalize()
        outfile.write(encrypted_chunk)
    
    return salt, file_hash

def decrypt_file_aes(input_path, output_path, password):
    """Decrypt a file using AES-256 with password-based key derivation"""
    with open(input_path, 'rb') as infile:
        # Read salt and IV from the beginning of the file
        salt = infile.read(16)
        iv = infile.read(16)
        
        # Read stored file hash
        stored_hash = infile.read(64).decode()  # SHA-256 hash is 64 chars in hex
        
        # Derive key from password and salt
        key, _ = derive_key(password, salt)
        
        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        
        # Create unpadder
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        
        # Read encrypted data
        encrypted_data = infile.read()
    
    # Decrypt data
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
    
    # Remove padding
    unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()
    
    # Write decrypted data to output file
    with open(output_path, 'wb') as outfile:
        outfile.write(unpadded_data)
    
    # Verify file integrity
    decrypted_hash = generate_file_hash(output_path)
    
    return decrypted_hash == stored_hash

# RSA encryption functions for secure sharing
def generate_rsa_key_pair():
    """Generate RSA key pair for secure file sharing"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    
    return private_key, public_key

def encrypt_with_rsa(data, public_key):
    """Encrypt data with RSA public key"""
    encrypted = public_key.encrypt(
        data,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted

def decrypt_with_rsa(encrypted_data, private_key):
    """Decrypt data with RSA private key"""
    decrypted = private_key.decrypt(
        encrypted_data,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted