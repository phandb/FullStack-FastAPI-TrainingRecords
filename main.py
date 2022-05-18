from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.responses import RedirectResponse

import models
from database import engine
from routers import auth, users, tasks

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")


# Route all normal url to /tasks
@app.get("/")
async def root():
    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
