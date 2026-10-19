import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import env

bearer = HTTPBearer()


def require_token(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> None:
    """Prüft `Authorization: Bearer <API_TOKEN>`. Wird pro Router als Dependency gesetzt."""
    if not secrets.compare_digest(creds.credentials, env.api_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")