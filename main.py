import os
import argparse
from tkinter import Tk, filedialog
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def pick_file(title="Select a file"):
    """Open a file picker and return the selected file path."""
    root = Tk()
    root.withdraw()  # Hide the main Tk window
    file_path = filedialog.askopenfilename(title=title)
    root.destroy()
    return file_path


def save_file(title="Save file as"):
    """Open a save dialog and return the output file path."""
    root = Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(title=title)
    root.destroy()
    return file_path


def encrypt_file(input_filepath: str, output_filepath: str, key: bytes):
    iv_length = 12
    chunk_size = 64 * 1024
    iv = get_random_bytes(iv_length)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)

    with open(input_filepath, 'rb') as infile, open(output_filepath, 'wb') as outfile:
        outfile.write(len(iv).to_bytes(1, 'big'))
        outfile.write(iv)

        while chunk := infile.read(chunk_size):
            outfile.write(cipher.encrypt(chunk))

        tag = cipher.digest()
        outfile.write(tag)


def decrypt_file(input_filepath: str, output_filepath: str, key: bytes):
    with open(input_filepath, 'rb') as infile:
        iv_length = int.from_bytes(infile.read(1), 'big')
        iv = infile.read(iv_length)
        infile.seek(0, os.SEEK_END)
        file_size = infile.tell()
        tag_position = file_size - 16
        infile.seek(1 + iv_length)

        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        chunk_size = 64 * 1024
        bytes_to_read = tag_position - (1 + iv_length)
        total_read = 0

        with open(output_filepath, 'wb') as outfile:
            while total_read < bytes_to_read:
                read_len = min(chunk_size, bytes_to_read - total_read)
                chunk = infile.read(read_len)
                total_read += len(chunk)
                outfile.write(cipher.decrypt(chunk))

        infile.seek(tag_position)
        tag = infile.read(16)

        try:
            cipher.verify(tag)
            print("✅ Decryption successful.")
        except ValueError:
            print("❌ Decryption failed: data is corrupted or tampered.")


def main():
    parser = argparse.ArgumentParser(description="AES-GCM File Encryptor")
    parser.add_argument('--key', help="32-byte (256-bit) hex key, or type 'gen' to generate one", default='gen')
    args = parser.parse_args()

    # Handle key
    if args.key == 'gen':
        key = get_random_bytes(32)
        print("🔑 Generated new key (hex):", key.hex())
    else:
        key = bytes.fromhex(args.key)
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes (256 bits)")

    print("\nChoose action:")
    print("[1] Encrypt a file")
    print("[2] Decrypt a file")
    choice = input("Enter 1 or 2: ")

    if choice == '1':
        input_file = pick_file("Select a file to encrypt")
        if not input_file:
            print("No file selected.")
            return
        output_file = save_file("Save encrypted file as")
        if not output_file:
            print("No output file specified.")
            return
        encrypt_file(input_file, output_file, key)
        print(f"🔐 Encrypted '{input_file}' ➝ '{output_file}'")

    elif choice == '2':
        input_file = pick_file("Select a file to decrypt")
        if not input_file:
            print("No file selected.")
            return
        output_file = save_file("Save decrypted file as")
        if not output_file:
            print("No output file specified.")
            return
        decrypt_file(input_file, output_file, key)
        print(f"🔓 Decrypted '{input_file}' ➝ '{output_file}'")

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
