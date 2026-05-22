import asyncio
import bcrypt
import hashlib
import base64

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher


BCRYPT_ROUNDS = 12

hasher = PasswordHash((
    BcryptHasher(rounds=BCRYPT_ROUNDS),
))


def _prepare_password(password: str) -> bytes:
    pw_bytes = password.encode("utf-8")
    sha256_hash = hashlib.sha256(pw_bytes).digest()
    return base64.b64encode(sha256_hash)


async def get_hash(password: str) -> str:
    hashed = await asyncio.to_thread(
        bcrypt.hashpw,
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    )

    return hashed.decode("utf-8")


async def verify_hash(plain_password: str, hashed_password: str) -> bool:
    return await asyncio.to_thread(
        bcrypt.checkpw,
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


async def main():
    raw_hash_1 = await get_hash('12345678')
    pwd_hash_1 = hasher.hash('12345678')

    print(await verify_hash('12345678', raw_hash_1))
    print(hasher.verify('12345678', pwd_hash_1))

    print(await verify_hash('12345678', pwd_hash_1))
    print(hasher.verify('12345678', raw_hash_1))

    print(pwd_hash_1)
    print(raw_hash_1)

    print (' ---- ')

    print(await get_hash('client_secret_1'))
    print(await get_hash('client_secret_2'))
    print(await get_hash('client_secret_3'))
    print(await get_hash('client_secret_4'))


asyncio.run(main())