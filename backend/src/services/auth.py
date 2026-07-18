from datetime import UTC, datetime, timedelta
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from config import Settings

_password_hasher = PasswordHasher()
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_COOKIE = "access_token"


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False


def create_access_token(user_id: UUID, settings: Settings) -> str:
    expires_at = datetime.now(UTC) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        subject = payload.get("sub")
        if not subject:
            raise JWTError("missing subject")
        return UUID(subject)
    except (JWTError, ValueError, TypeError) as exc:
        raise JWTError("invalid token") from exc
