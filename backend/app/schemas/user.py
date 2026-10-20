from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Self-registration. Only customer accounts can be created this way."""

    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None
    # Kept so that a request for a staff role gets a clear error instead of
    # silently becoming a customer account.
    role: UserRole = UserRole.CUSTOMER


class AdminUserCreate(BaseModel):
    """An admin creating an account with any role."""

    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None
    role: UserRole


class RoleUpdate(BaseModel):
    role: UserRole


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    company_name: Optional[str]
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
