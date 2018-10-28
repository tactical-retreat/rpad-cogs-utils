from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def encode(plain_text):
    backend = default_backend()
    key = "201302DNTMYQUEST".encode('utf-8')
    iv = bytes([0] * 16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plain_text.encode('utf-8')) + padder.finalize()

    msg_encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return msg_encrypted.hex()


def decode(hex_text):
    backend = default_backend()
    key = "201302DNTMYQUEST".encode('utf-8')
    iv = bytes([0] * 16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    hex_array = bytearray.fromhex(hex_text)
    msg_bytes = decryptor.update(bytes(hex_array)) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    msg_bytes = unpadder.update(msg_bytes) + unpadder.finalize()
    msg_string = msg_bytes.decode('utf-8')
    return msg_string
