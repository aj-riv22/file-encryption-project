# Secure File Encryption Project

A web application for securely encrypting, storing, and sharing files using AES-256 encryption.

## Features

- **User Authentication**: Secure registration and login system
- **AES-256 Encryption**: Industry-standard encryption for all files
- **File Integrity Verification**: Ensures files haven't been tampered with
- **Secure File Sharing**: Share encrypted files with specific users
- **Access Control**: Control who can access your encrypted files
- **Audit Logging**: Track all file operations for security monitoring

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite
- **Encryption**: Python Cryptography library
- **Frontend**: Bootstrap 5, JavaScript
- **Authentication**: Flask-Login

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/file-encryption-project.git
cd file-encryption-project
```
2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

3. install dependencies
pip install -r requirements.txt
4. Set up environment variables:
echo "SECRET_KEY=$(python -c 'import os; print(os.urandom(24).hex())')" > .env

5. Run the application:
```bash
python3 run.py
```