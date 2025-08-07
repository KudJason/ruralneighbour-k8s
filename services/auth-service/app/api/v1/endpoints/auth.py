from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.schemas.token import Token, TokenPayload
from app.services.auth_service import AuthService
from app.core.security import create_access_token, SECRET_KEY, ALGORITHM
from app.db.session import get_db
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = AuthService.register_user(db, user_in)
    return user


@router.post("/login", response_model=Token)
def login(request: Request, user_in: UserLogin, db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    access_token = create_access_token(subject=str(user.user_id))
    return Token(access_token=access_token)


@router.get("/me", response_model=TokenPayload)
def get_me(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token"
        )
    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role", "user")
        exp = payload.get("exp")
        if user_id is None or exp is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    return TokenPayload(sub=user_id, exp=int(exp), role=role)
