from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import models
from database import engine
from routers import auth, users, tasks

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
