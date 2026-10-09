# app/routers/auth_router.py
import re
from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..schemas.auth_schemas import ChangePasswordRequest

router = APIRouter()

login_attempts = {}
MAX_ATTEMPTS = 5
BLOCK_DURATION_MINUTES = 15


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    username = form_data.username
    if username in login_attempts:
        record = login_attempts[username]
        if record["blocked_until"] and now < record["blocked_until"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos fallidos. Cuenta bloqueada temporalmente por 15 minutos."
            )
        if record["blocked_until"] and now >= record["blocked_until"]:
            login_attempts[username] = {"count": 0, "blocked_until": None}

    user = authenticate_user(db, username, form_data.password)
    if not user:
        if username not in login_attempts:
            login_attempts[username] = {"count": 1, "blocked_until": None}
        else:
            login_attempts[username]["count"] += 1

        if login_attempts[username]["count"] >= MAX_ATTEMPTS:
            login_attempts[username]["blocked_until"] = now + timedelta(minutes=BLOCK_DURATION_MINUTES)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos fallidos. Cuenta bloqueada temporalmente por 15 minutos."
            )
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")

    if username in login_attempts:
        del login_attempts[username]

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


def validate_strong_password(password: str) -> None:
    """Valida que la contraseña sea robusta. Lanza HTTPException si no cumple."""
    errors = []
    if len(password) < 8:
        errors.append("mínimo 8 caracteres")
    if not re.search(r"[A-Z]", password):
        errors.append("al menos una letra mayúscula")
    if not re.search(r"[a-z]", password):
        errors.append("al menos una letra minúscula")
    if not re.search(r"\d", password):
        errors.append("al menos un número")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", password):
        errors.append("al menos un carácter especial (!@#$%^&*...)")
    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"La contraseña no es suficientemente robusta: {', '.join(errors)}",
        )


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña antigua es incorrecta")

    if request.old_password == request.new_password:
        raise HTTPException(
            status_code=400,
            detail="La nueva contraseña debe ser diferente a la anterior",
        )

    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Las contraseñas nuevas no coinciden",
        )

    validate_strong_password(request.new_password)

    current_user.password_hash = hash_password(request.new_password)
    current_user.is_active = True 
    current_user.is_default_password = False

    db.add(current_user)
    db.commit()

    return {"message": "Contraseña actualizada exitosamente"}
