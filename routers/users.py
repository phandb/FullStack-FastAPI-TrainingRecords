from fastapi import APIRouter, Depends, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse, HTMLResponse
from starlette.templating import Jinja2Templates

import models
from database import engine, SessionLocal
from routers.auth import get_current_user, verify_password, get_password_hashed, get_user_exception

import sys
sys.path.append("..")


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not Found!"}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


# Setup database
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


# Create User model for verification
class UserVerification(BaseModel):
    username: str
    password: str
    new_password: str


# --------Users API Endpoints --------------
@router.get("/edit-password", response_class=HTMLResponse)
async def edit_user_view(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("edit-password.html", {"request": request, "user": user})


@router.post("/edit-password", response_class=HTMLResponse)
async def user_password_change(request: Request,
                               username: str = Form(...),
                               password: str = Form(...),
                               password2: str = Form(...),
                               db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_data = db.query(models.Users).filter(models.Users.username == username).first()

    msg = "invalid username or password"

    if user_data is not None:
        if username == user_data.username and verify_password(password, user_data.hashed_password):
            user_data.hashed_password = get_password_hashed(password2)
            db.add(user_data)
            db.commit()
            msg = "Password Updated"

    return templates.TemplateResponse("edit-password.html", {"request": request, "user": user, "msg": msg})


@router.put("/password")
async def update_user_password(user_verification: UserVerification,
                               user: dict = Depends(get_current_user),
                               db: Session = Depends(get_db)):
    # Validate logged in user
    if user is None:
        # return get_user_exception()
        return None

    # Retrieve the current user info and put them into a variable
    user_model = db.query(models.Users).filter(models.Users.id == user.get("id")).first()

    # Validate the current user against the User Verification
    if user is not None:
        if user_verification.username == user_model.username and verify_password(
                user_verification.password, user_model.hashed_password):
            #  Update password
            user_model.hashed_password = get_password_hashed(user_verification.new_password)
            db.add(user_model)
            db.commit()
            return 'Successful'
        return 'Invalid user or request'


@router.delete("/")
async def delete_user(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if user is None:
        return get_user_exception()
        # return None

    user_model = db.query(models.Users).filter(models.Users.id == user.get("id")).first()

    if user_model is None:
        return "Invalid user or request"

    db.query(models.Users).filter(models.Users.id == user.get("id")).delete()
    db.commit()

    return 'Delete Successful'

