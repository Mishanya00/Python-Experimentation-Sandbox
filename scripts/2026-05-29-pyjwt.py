from datetime import datetime, timedelta, UTC
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


class TokenService():
    def __init__(self, jwt_secret: str, algorithm: str):
        self._jwt_secret = jwt_secret
        self._algorithm = algorithm

    def encode_jwt(self, payload: dict, expire: int) -> str:
        expire = datetime.now(UTC) + timedelta(seconds=expire)
        to_encode = {
            **payload,
            "exp": expire,
        }
        encoded = jwt.encode(payload=to_encode, key=self._jwt_secret, algorithm=self._algorithm)

        return encoded

    def decode_jwt(self, token: str | bytes) -> dict[str, Any]:
        try:
            decoded = jwt.decode(
                jwt=token, key=self._jwt_secret, algorithms=[self._algorithm], options={"verify_signature": True}
            )
        except (ExpiredSignatureError, InvalidTokenError):
            raise ValueError

        return decoded


ts = TokenService(jwt_secret="a-string-secret-at-least-256-bits-long", algorithm="HS256")

a = ts.encode_jwt(payload={'user_id': 123}, expire=3600)
b = ts.encode_jwt(payload={'user_id': 123, 'role': 'admin'}, expire=300)

decoded_a = ts.decode_jwt(a)
decoded_b = ts.decode_jwt(b)

# print(a)
# print(b)
# print(decoded_a)
# print(decoded_b)


print(ts.decode_jwt(b'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkxvcmQiLCJhZG1pbiI6ZmFsc2V9.kQ4s4q-uxP0CFXdmXCJTh9s4Nn5wC0mgDLS_r0-DSGg'))