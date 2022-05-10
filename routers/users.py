from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import engine, SessionLocal
from routers.auth import get_current_user, get_user_exception, verify_password, get_password_hashed

import sys
sys.path.append("..")


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not Found!"}}
)

models.Base.metadata.create_all(bind=engine)


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
@router.get("/")
async def read_all_users(db: Session = Depends(get_db)):
    return db.query(models.Users).all()


@router.get("/{user_id}")
async def read_user_by_path_param(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user_model is not None:
        return user_model
    return "Invalid User"


"""
@router.get("/")
async def read_user_by_query_param(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user_model is not None:
        return user_model
    return "Invalid User"
"""


@router.put("/password")
async def update_user_password(user_verification: UserVerification,
                               user: dict = Depends(get_current_user),
                               db: Session = Depends(get_db)):
    # Validate logged in user
    if user is None:
        return get_user_exception()

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

    user_model = db.query(models.Users).filter(models.Users.id == user.get("id")).first()

    if user_model is None:
        return "Invalid user or request"

    db.query(models.Users).filter(models.Users.id == user.get("id")).delete()
    db.commit()

    return 'Delete Successful'

