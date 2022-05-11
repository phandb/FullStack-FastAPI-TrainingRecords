from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import engine, SessionLocal
from routers.auth import get_current_user, get_user_exception

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not Found"}}
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Task(BaseModel):
    task_name: str
    category: str
    date_taken: datetime


# -------CRUD API Endpoint-------
# Read all tasks for all users
@router.get("/")
async def read_all_tasks(db: Session = Depends(get_db)):
    return db.query(models.Tasks).all()


# Read all task for current user
@router.get("/user")
async def read_user_all_tasks(user: dict = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    # Validate user
    if user is None:
        raise get_user_exception()
    # get all tasks
    return db.query(models.Tasks) \
        .filter(models.Tasks.owner_id == user.get("id")) \
        .all()


# Read specific task for current user
@router.get("/{task_id}")
async def read_task(task_id: int,
                    user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    # validate user
    if user is None:
        raise get_user_exception()
    # Retrieve the task
    task_model = db.query(models.Tasks)\
        .filter(models.Tasks.id == task_id)\
        .filter(models.Tasks.owner_id == user.get("id")) \
        .first()
    # Check for the task
    if task_model is not None:
        return task_model
    raise http_exception()


# Create a task for current user
@router.post("/")
async def create_task(task: Task,
                      user: dict = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    # Validate the user
    if user is None:
        raise get_user_exception()
    # Create model to hold task object
    task_model = models.Tasks()

    # Save task info from entry point to the object
    task_model.task_name = task.task_name
    task_model.category = task.category
    task_model.date_taken = task.date_taken
    task_model.owner_id = user.get("id")

    # Save object to database
    db.add(task_model)
    db.commit()

    return {
        'status': 201,
        'transaction': 'Successful'
    }


# Update task for current user
@router.put("/{task_id}")
async def update_task(task_id: int,
                      task: Task,
                      user: dict = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    # Validate the user
    if user is None:
        raise get_user_exception()
    # Retrieve the task to update
    task_model = db.query(models.Tasks)\
        .filter(models.Tasks.id == task_id)\
        .filter(models.Tasks.owner_id == user.get("id"))\
        .first()

    # Validate the task
    if task_model is None:
        raise http_exception()

    # Update the task
    task_model.task_name = task.task_name
    task_model.category = task.category
    task_model.date_taken = task.date_taken

    # Save changes to database
    db.add(task_model)
    db.commit()

    return {
        'status': 200,
        'transaction': 'Successful'
    }


# Delete a task for current user
@router.delete("/{task_id}")
async def delete_task(task_id: int,
                      user: dict = Depends(get_current_user),
                      db: Session = Depends(get_db)):

    # Validate user
    if user is None:
        raise get_user_exception()

    # Retrieve the task by id
    task_model = db.query(models.Tasks)\
        .filter(models.Tasks.id == task_id)\
        .first()

    # Validate the task to be deleted
    if task_model is None:
        raise http_exception()

    # delete task in database
    db.query(models.Tasks).filter(models.Tasks.id == task_id).delete()

    db.commit()

    return {
        'status': 200,
        'transaction': 'Successful'
    }


def http_exception():
    return HTTPException(status_code=404, detail="Task not found")