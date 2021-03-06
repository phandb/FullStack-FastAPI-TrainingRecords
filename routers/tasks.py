from datetime import datetime, timedelta
from enum import Enum

from fastapi import APIRouter, Depends, Request, Form
from jinja2 import Template
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import RedirectResponse

import models
from database import engine, SessionLocal
from routers.auth import get_current_user

import sys

sys.path.append("..")

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not Found"}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


# datetime_template = Template("{{ date.strftime('%Y-%m-%d') }}")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Category(str, Enum):
    EXTRACT = "Extract"
    ANALYSIS = "Analysis"
    FULL_METHOD = "Full Method"


class Method(str, Enum):
    EPA_504_1 = "504.1"
    Aroclor = "508.1 Aroclor"
    Chlordane = "508.1 Chlordane"
    Pesticides = "508.1 Pesticides"
    Pesticides_Sublist = "508.1 Pesticides-Sublist"
    TCEQ_Ind_List = "508.1 TCEQ-Ind-List"
    Toxaphene = "508.1 Toxaphene"
    PCB_as_DCB = "508A PCB as DCB"
    EPA_515_4 = "515.4"
    THM = "524.2 THM"
    VOC = "524.2 VOC"
    Endrin = "525.2 Endrin"
    SOC5 = "525.2 SOC5"
    Carbamates = "531.1 Carbamates"
    Glyphosate_547 = "547 Glyphosate"
    Glyphosate_548 = "548.1 Glyphosate"
    Endothall = "548.1 Endothall"
    Para_Diq = "549.2 Para/Diq"
    HAA = "552.2 HAA"


# ---------- Rebuild Entire API for full stack project-----------
@router.get("/", response_class=HTMLResponse)
async def read_all_by_user(request: Request, db: Session = Depends(get_db)):
    # get current user
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    task_model = models.Tasks()

    tasks = db.query(models.Tasks).filter(models.Tasks.owner_id == user.get("id")).order_by(models.Tasks.task_name)

    # Update number days to expire for each record
    for index, task in enumerate(tasks):
        tasks[index].days_expired = await get_days_to_expire(tasks[index].date_expired)
    #     task_model.days_expired = tasks[index].days_expired
    #     task_model.owner_id = user.get("id")
    #     db.add(task_model)
    #
    # db.commit()
    return templates.TemplateResponse("home.html", {"request": request, "tasks": tasks, "user": user})


# call add-task.html
@router.get("/add-task", response_class=HTMLResponse)
async def add_new_task(request: Request):
    # get the current user
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("add-task.html", {"request": request,
                                                        "methods": [m.value for m in Method],
                                                        "categories": [c.value for c in Category],
                                                        "user": user})


# process form in add-task.html
@router.post("/add-task", response_class=HTMLResponse)
async def create_task(request: Request,
                      # task_name: str = Form(...),
                      task_name: Method = Form(...),
                      category: Category = Form(...),
                      date_taken: datetime = Form(...),
                      db: Session = Depends(get_db)):
    #  The parameters must be matched to the name field of the form in add-task.html

    # Get the current user
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    task_model = models.Tasks()

    task_model.task_name = task_name
    task_model.category = category
    task_model.date_taken = date_taken
    task_model.date_expired = await set_expire_date(date_taken)
    task_model.days_expired = await get_days_to_expire(task_model.date_expired)
    task_model.owner_id = user.get("id")

    # Validate Task -- No duplicate task name and category allowed

    tasks = db.query(models.Tasks).filter(models.Tasks.owner_id == user.get("id")).all()

    for index, task in enumerate(tasks):
        if task_model.task_name == tasks[index].task_name and task_model.category == tasks[index].category:
            msg = "The selected task with the category already exists.  Please choose different task or category."
            # return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND, headers=msg)
            return templates.TemplateResponse("add-task.html", {"request": request,
                                                                "methods": [m.value for m in Method],
                                                                "categories": [c.value for c in Category],
                                                                "user": user,
                                                                "msg": msg})

    db.add(task_model)
    db.commit()

    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)


@router.get("/edit-task/{task_id}", response_class=HTMLResponse)
async def edit_task(request: Request, task_id: int, db: Session = Depends(get_db)):
    # Get the current user
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    task = db.query(models.Tasks).filter(models.Tasks.id == task_id).first()
    msg = "Do not change the task or category.  No task with the same category is allowed!"
    return templates.TemplateResponse("edit-task.html", {"request": request,
                                                         "methods": [m.value for m in Method],
                                                         "categories": [c.value for c in Category],
                                                         "task": task,
                                                         "user": user,
                                                         "msg": msg})


@router.post("/edit-task/{task_id}", response_class=HTMLResponse)
async def edit_task_commit(request: Request,
                           task_id: int,
                           # task_name: str = Form(...),
                           task_name_selected: Method = Form(...),
                           category_selected: Category = Form(...),
                           date_taken: datetime = Form(...),
                           db: Session = Depends(get_db)):
    # get the current user
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    # Validate Task -- No duplicate task name and category allowed

    # tasks = db.query(models.Tasks).filter(models.Tasks.owner_id == user.get("id")).all()
    #
    # for index, task in enumerate(tasks):
    #     if task_name_selected != tasks[index].task_name and category_selected != tasks[index].category:
    #         msg = "The selected task with the category already exists.  No task with the same category is allowed!"
    #         return templates.TemplateResponse("edit-task.html", {"request": request,
    #                                                              "methods": [m.value for m in Method],
    #                                                              "categories": [c.value for c in Category],
    #                                                              "task": task,
    #                                                              "user": user,
    #                                                              "msg": msg})
    #
    # # Validate succeed then commit the changes to database

    task_model = db.query(models.Tasks).filter(models.Tasks.id == task_id).first()

    task_model.task_name = task_name_selected
    task_model.category = category_selected
    task_model.date_taken = date_taken
    task_model.date_expired = await set_expire_date(date_taken)

    db.add(task_model)
    db.commit()

    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)


@router.get("/delete/{task_id}")
async def delete_task(request: Request, task_id: int, db: Session = Depends(get_db)):
    # Get the current user
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    task_model = db.query(models.Tasks) \
        .filter(models.Tasks.id == task_id) \
        .filter(models.Tasks.owner_id == user.get("id")) \
        .first()

    if task_model is None:
        return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)

    db.query(models.Tasks).filter(models.Tasks.id == task_id).delete()

    db.commit()

    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)


async def get_days_to_expire(expired_date: datetime):
    # Format datetime
    date_format_str = "%Y-%m-%d"

    # date_taken = datetime.strftime(date_taken, date_format_str)

    # Get interval between to dates in seconds
    days_to_expire = (expired_date - datetime.today()).days
    # seconds_to_expire = (expired_date - datetime.today()).total_seconds()
    # seconds_remain = seconds_to_expire % 864000

    expireddate = expired_date.strftime(date_format_str)
    todaydate = datetime.today().strftime(date_format_str)

    if todaydate < expireddate:
        return str(abs(days_to_expire) + 1)  # duration in days
    if todaydate == expireddate:
        return "< 1"
    else:
        return "expired"


async def set_expire_date(date_taken: datetime):
    return date_taken + timedelta(days=2)


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
