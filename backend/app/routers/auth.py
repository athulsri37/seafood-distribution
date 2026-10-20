from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserOut, Token, LoginRequest
from app.services.users import EmailAlreadyRegistered, create_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sign-up creates customer accounts only. "
            "Ask an admin to create a distributor or admin account.",
        )
    try:
        user = create_user(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            company_name=payload.company_name,
            role=UserRole.CUSTOMER,
        )
    except EmailAlreadyRegistered:
        raise HTTPException(status_code=400, detail="Email already registered")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token, user=UserOut.model_validate(user))


def _authenticate(db: Session, email: str, password: str) -> Token:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Invalid email or password", headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return _authenticate(db, payload.email, payload.password)


@router.post("/token", response_model=Token)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """The OAuth2 password flow, which Swagger UI's Authorize button uses.

    Same check as `/login`, but it takes a form with the email in `username`, as the OAuth2
    spec requires. The app itself uses `/login`.
    """
    return _authenticate(db, form.username, form.password)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
