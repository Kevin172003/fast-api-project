from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ..models import Users
from passlib.context import CryptContext 
from ..db import SessionLocal
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/auth",
    tags=["tags"]
)

SECRET_KEY = "abcdefghijklmnopqrstuvwxyz1234567890"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

router.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='templates')

# PAGES
@router.get("/login-page")
def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register-page")
def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# END POINTS
def auth_user(user_name: str, password: str, db: Session):
    user = db.query(Users).filter(Users.username == user_name).first()
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    payload = {"sub": username, "id": user_id, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# async def get_current_user(token: Annotated[str, Depends(oauth_bearer)]):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         user_id: int = payload.get("id")
#         user_role: str = payload.get("role")
#         if username is None or user_id is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 detail="Could not validate user.")
#         print(username, "user id", user_id)
#         return {"username": username, "id": user_id, "user_role": user_role}
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Could not validate user.")
async def get_current_user(token: str):
    if not token:
        print("No token found!")  # Debugging
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = {
            "id": payload.get("id"),
            "username": payload.get("sub"),
            "role": payload.get("role"),
        }
        print(f"Extracted user from token: {user}")  # Debugging
        return user
    except JWTError as e:
        print(f"JWT decode error: {e}")  # Debugging
        return None


@router.post("/token")
async def login_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = auth_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.username, user.id, user.role, timedelta(hours=1))  # Increase validity

    print(f"Generated token: {token}")  # Debugging

    response = RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


