from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole


class EmailAlreadyRegistered(Exception):
    pass


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    company_name: Optional[str],
    role: UserRole,
) -> User:
    """Create an account. Callers decide which roles they're allowed to grant."""
    if db.query(User).filter(User.email == email).first():
        raise EmailAlreadyRegistered(email)

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        company_name=company_name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
