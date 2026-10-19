from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User, UserRole
from app.schemas.user import AdminUserCreate, RoleUpdate, UserOut
from app.services.users import EmailAlreadyRegistered, create_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_as_admin(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    try:
        return create_user(db, **payload.model_dump())
    except EmailAlreadyRegistered:
        raise HTTPException(status_code=400, detail="Email already registered")


@router.patch("/{user_id}/role", response_model=UserOut)
def change_user_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # An admin who demoted themselves could leave the platform with no admin at all.
    if user.id == current_user.id and payload.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=400,
            detail="You can't remove your own admin role. Ask another admin to change it.",
        )

    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
