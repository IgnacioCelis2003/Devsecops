# app/routers/users_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User, UserInteraction
from ..auth import get_current_user, get_current_user_enforcing_password_change, require_admin, hash_password
from ..schemas.user_schemas import NewUserRequest, UpdateUserRequest

router = APIRouter()


@router.get("/me")
def get_user_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "is_default_password": current_user.is_default_password,
        "role": current_user.role or "admin",
        "tags": current_user.tags or [],
    }


@router.post("")
def create_user(
    request: NewUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya esta ocupado. Elige otro.")

    new_user = User(
        username=request.username, 
        password_hash=hash_password(request.password),
        is_default_password=True,
        is_active=True,
        role=request.role or "viewer",
        tags=request.tags or [],
    )
    db.add(new_user)
    db.commit()
    return {"message": "Usuario creado"}


@router.get("")
def list_users(
    current_user: User = Depends(get_current_user_enforcing_password_change), db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return [{
        "id": u.id,
        "username": u.username,
        "role": u.role or "admin",
        "tags": u.tags or [],
        "is_active": u.is_active,
    } for u in users]


@router.put("/{user_id}")
def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if request.role is not None:
        user.role = request.role
    if request.tags is not None:
        user.tags = request.tags
    if request.is_active is not None:
        user.is_active = request.is_active
    db.commit()
    return {"message": "Usuario actualizado exitosamente"}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.execute(delete(UserInteraction).where(UserInteraction.user_id == user_id))
    db.delete(user)
    db.commit()
    return {"message": "Usuario eliminado"}
