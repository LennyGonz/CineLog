"""
Auth helpers for Supabase JWT verification.
"""

from dataclasses import dataclass
from typing import Optional, Sequence
from uuid import UUID
import os

import jwt
from jwt import PyJWKClient
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .data import edit


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: Optional[str]


def _audiences() -> Sequence[str]:
    raw = os.getenv("SUPABASE_JWT_AUD", "authenticated")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or ["authenticated"]


def _jwks_url() -> Optional[str]:
    url = os.getenv("SUPABASE_JWKS_URL")
    if url:
        return url
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        return None
    return supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"


_jwk_client: Optional[PyJWKClient] = None


def _get_jwk_client() -> Optional[PyJWKClient]:
    global _jwk_client
    jwks_url = _jwks_url()
    if not jwks_url:
        return None
    if _jwk_client is None:
        headers = {}
        anon_key = os.getenv("SUPABASE_ANON_KEY")
        if anon_key:
            headers["apikey"] = anon_key
        _jwk_client = PyJWKClient(jwks_url, headers=headers or None)
    return _jwk_client


def _decode_token(token: str) -> dict:
    audiences = _audiences()
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

    if jwt_secret:
        # Local/dev fallback when using a symmetric JWT secret.
        return jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience=audiences if len(audiences) > 1 else audiences[0],
        )

    jwk_client = _get_jwk_client()
    if not jwk_client:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL or SUPABASE_JWKS_URL must be set for JWT verification",
        )

    signing_key = jwk_client.get_signing_key_from_jwt(token).key
    return jwt.decode(
        token,
        signing_key,
        algorithms=["RS256", "ES256"],
        audience=audiences if len(audiences) > 1 else audiences[0],
    )


def get_current_user(
    db: Session = Depends(get_db), authorization: Optional[str] = Header(None)
) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    try:
        payload = _decode_token(token)
    except jwt.PyJWTError as e:
        detail = "Invalid token"
        if os.getenv("DEBUG", "false").lower() == "true":
            detail = f"Invalid token: {e}"
        raise HTTPException(status_code=401, detail=detail)

    user_sub = payload.get("sub")
    if not user_sub:
        raise HTTPException(status_code=401, detail="Token missing subject")

    try:
        user_uuid = UUID(user_sub)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid subject UUID")

    email = payload.get("email")
    edit.create_or_get_user_by_id(db, user_uuid, email=email)
    db.commit()

    return AuthUser(id=str(user_uuid), email=email)
