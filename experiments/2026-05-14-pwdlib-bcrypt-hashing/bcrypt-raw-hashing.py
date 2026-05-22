import asyncio
import bcrypt
import hashlib
import base64


BCRYPT_ROUNDS = 12


def _prepare_password(password: str) -> bytes:
    pw_bytes = password.encode("utf-8")
    sha256_hash = hashlib.sha256(pw_bytes).digest()
    return base64.b64encode(sha256_hash)


async def get_hash(password: str) -> str:
    pre_hashed = _prepare_password(password)

    hashed = await asyncio.to_thread(
        bcrypt.hashpw,
        pre_hashed,
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    )

    return hashed.decode("utf-8")


async def verify_hash(plain_password: str, hashed_password: str) -> bool:
    pre_hashed = _prepare_password(plain_password)

    return await asyncio.to_thread(
        bcrypt.checkpw,
        pre_hashed,
        hashed_password.encode("utf-8")
    )


async def main():
    hash1 = await get_hash('12345678')
    print(hash1)


asyncio.run(main())