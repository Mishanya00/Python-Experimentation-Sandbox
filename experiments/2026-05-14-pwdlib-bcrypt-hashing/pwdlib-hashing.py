from pwdlib import PasswordHash, exceptions
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher


password_hash = PasswordHash((
    BcryptHasher(rounds=12),
))

# hash1 = password_hash.hash('12345678')
# hash2 = password_hash.hash('12345678')
# hash3 = password_hash.hash('12345678')
# hash4 = password_hash.hash('12345678')
#
# print(hash1)
# print(hash2)
# print(hash3)
# print(hash4)
#
# print(password_hash.verify("12345678", hash1))
# print(password_hash.verify("12345678", hash2))
# print(password_hash.verify("12345678", hash3))
# print(password_hash.verify("12345678", hash4))

print(password_hash.verify("12345678", '$2b$12$ydbi6gpnnvc0Ag6jNnrGcODId0zfOIq7FL0AcH/n4CTBekZRrzjwu'))

