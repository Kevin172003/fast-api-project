from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from .models import Base 
from .db import engine
from .routers import auth, todos, admin, users
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

app = FastAPI()


Base.metadata.create_all(bind=engine)



app.mount("/static", StaticFiles(directory="static"), name="static")




@app.get("/")
def health_check(request: Request):
    return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)



app.include_router(auth.router)

app.include_router(todos.router)

app.include_router(admin.router)

app.include_router(users.router)

