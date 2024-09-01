from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import models
from app.schemas import schemas
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError


router = APIRouter(prefix="/auth", tags=["Authentication Routes"])
templates = Jinja2Templates(directory="app/templates")

SECRET_KEY = "46e27227d9f8613527811f500db59f34"
ALGORITHM = "HS256"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

db_dependency = Annotated[Session, Depends(get_db)]

### Pages Endpoints

@router.get('/login-page')
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {'request': request})


@router.get('/register-page')
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {'request': request})



### Backend API Endpoints
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str, db: Session) -> bool | models.Users:
    db_user = db.query(models.Users).filter_by(username=username).first()
    if not db_user:
        return False
    if not verify_password(password, db_user.hashed_password):
        return False
    return db_user


def create_access_token(
    username: str, id: int, role: str, expires_delta: timedelta | None = None
) -> str:
    to_encode = {"sub": username, "id": id, "role": role}
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user.",
            )
        return {"username": username, "id": user_id, "user_role": user_role}
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user."
        )




@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user."
        )
    token = create_access_token(
        user.username, user.id, user.role, timedelta(minutes=20)
    )

    return {"access_token": token, "token_type": "bearer"}


@router.post("/create-user", status_code=status.HTTP_201_CREATED)
async def create_user(
    db: db_dependency, create_user_request: schemas.CreateUserRequest
):
    db_user = (
        db.query(models.Users).filter_by(username=create_user_request.username).first()
    )
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with username {create_user_request.username} already exists. Please try with another username.",
        )
    db_user = db.query(models.Users).filter_by(email=create_user_request.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {create_user_request.email} already exists. Please try with another email.",
        )
    create_user_model = models.Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=get_password_hash(create_user_request.password),
        is_active=True,
        phone_number=create_user_request.phone_number,
    )
    db.add(create_user_model)
    db.commit()
