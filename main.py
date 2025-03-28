from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

salt = b'5f\xb4\x93\x9b\xa4\xb2\xdb\xb5+\xa3\xf1\x84,\xd4\x88h\xbd\x18ak\x97Zu\xaf\xe4\xc6\xbek5\xd4\x11'
password = "password"

key = PBKDF2(password, salt, dkLen=32)
print(key)

message = b"hello secret world"

cipher = AES.new(key, AES.MODE_CBC)
ciphered_data = cipher.encrypt(pad(message, AES.block_size))

print(ciphered_data)

with open('encrypted.bin', 'wb') as f:
    f.write(cipher.iv)
    f.write(ciphered_data)

with open('encrypted.bin', 'rb') as f:
    iv = f.read(16)
    decrypt_data = f.read()

cipher = AES.new(key, AES.MODE_CBC, iv = iv)
original = unpad(cipher.decrypt(decrypt_data), AES.block_size)
print(original)

with open('key.bin', 'wb') as f:
    f.write(key)




