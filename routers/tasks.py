from datetime import datetime

from fastapi import APIRouter, Depends, Request, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import RedirectResponse

import models
from database import engine, SessionLocal
from routers.auth import get_current_user, get_user_exception

import sys

sys.path.append("..")

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not Found"}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


# ---------- Rebuild Entire API for full stack project-----------
@router.get("/", response_class=HTMLResponse)
async def read_all_by_user(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(models.Tasks).filter(models.Tasks.owner_id == 1).all()
    return templates.TemplateResponse("home.html", {"request": request, "tasks": tasks})


# call add-task.html
@router.get("/add-task", response_class=HTMLResponse)
async def add_new_task(request: Request):
    return templates.TemplateResponse("add-task.html", {"request": request})


# process form in add-task.html
@router.post("/add-task", response_class=HTMLResponse)
async def create_task(request: Request,
                      name: str = Form(...),
                      category: str = Form(...),
                      db: Session = Depends(get_db)):
    #  The parameters must be matched to the name field of the form in add-task.html

    task_model = models.Tasks()

    task_model.task_name = name
    task_model.category = category
    task_model.date_taken = datetime.utcnow()
    task_model.owner_id = 1

    db.add(task_model)
    db.commit()

    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)


@router.get("/edit-task/{task_id}", response_class=HTMLResponse)
async def edit_task(request: Request, task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Tasks).filter(models.Tasks.id == task_id).first()

    return templates.TemplateResponse("edit-task.html", {"request": request, "task": task})


@router.post("/edit-task/{task_id}", response_class=HTMLResponse)
async def edit_task_commit(request: Request, task_id: int,
                           name: str = Form(...),
                           category: str = Form(...),
                           date_taken: datetime = Form(...),
                           db: Session = Depends(get_db)):
    task_model = db.query(models.Tasks).filter(models.Tasks.id == task_id).first()

    task_model.task_name = name
    task_model.category = category
    task_model.date_taken = date_taken

    db.add(task_model)
    db.commit()

    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)


@router.get("/delete/{task_id}")
async def delete_task(request: Request, task_id: int, db: Session = Depends(get_db)):

    task_model = db.query(models.Tasks)\
        .filter(models.Tasks.id == task_id)\
        .filter(models.Tasks.owner_id == 1)\
        .first()

    if task_model is None:
        return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)

    db.query(models.Tasks).filter(models.Tasks.id == task_id).delete()

    db.commit()

    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)


# -----------------------------------------------------

"""

# The following codes are for REST API and not for Full Stack Project

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
"""
