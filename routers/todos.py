from fastapi import APIRouter, Depends, HTTPException, Header, Path, Request, status, Form
from pydantic import BaseModel, Field
from ..models import Todos
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from ..db import SessionLocal
from .auth import get_current_user
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

templates = Jinja2Templates(directory='templates')

router = APIRouter(
    prefix="/todos",
    tags=["todos"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class TodoRequest:
    def __init__(
        self,
        title: str = Form(...),
        description: str = Form(...),
        priority: int = Form(...),
        complete: bool = Form(...)
    ):
        self.title = title
        self.description = description
        self.priority = priority
        self.complete = complete
# class TodoRequest(BaseModel):
#     title: str = Form(min_length=3)
#     description: str = Form(min_length=3, max_length=100)
#     priority: int = Form(gt=0, lt=6)
#     complete: bool = Form(...)

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access-token")
    return redirect_response

# PAGES
@router.get("/todo-page")
async def render_todo_page(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    
    if not token:
        return redirect_to_login()
    
    user = await get_current_user(token)
    if user is None:
        return redirect_to_login()

    todos = db.query(Todos).filter(Todos.owner_id == user.get("id")).all()
    
    return templates.TemplateResponse("todos.html", {"request": request, "todos": todos, "user": user})


@router.get("/add-todo-page")
async def render_add_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})
    except:
        return redirect_to_login()

@router.get("/edit-todo/{todo_id}")
async def render_edit_todo_page(todo_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        token = request.cookies.get("access_token")
        print(f"Token received: {token}")  # Debugging

        user = await get_current_user(token)
        print(f"User: {user}")  # Debugging

        if user is None:
            print("User not found or token invalid.")  # Debugging
            return RedirectResponse(url="/auth/login-page")

        owner_id = int(user.get("id"))
        todo = db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == owner_id).first()

        if not todo:
            print(f"Todo not found for ID: {todo_id}")  # Debugging
            raise HTTPException(status_code=404, detail="Todo not found")

        return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})

    except HTTPException as http_exception:
        print(f"HTTP Exception: {http_exception.detail}")  # Debugging
        raise http_exception  # Keep the actual HTTP error
    except Exception as e:
        print(f"Unhandled Exception in render_edit_todo_page: {e}")  # Debugging
        return RedirectResponse(url="/auth/login-page")




# END POINTS
@router.get("/all", status_code=status.HTTP_200_OK)
async def read_all(request: Request, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    todos = db.query(Todos).filter(Todos.owner_id == user.get("id")).all()
    return templates.TemplateResponse("todos.html", {"request": request, "todos": todos})

@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    todo_model = db.query(Todos).filter(Todos.id == todo_id)\
        .filter(Todos.owner_id == user.get("id")).first()
    if todo_model is not None:
        return todo_model
    else:
        raise HTTPException(status_code=404, detail="Todo not found.")

@router.get("/form")
def show_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@router.post("/todo")
async def create_todo(
    request: Request,
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    print("Received Form Data:", form_data)

    title = form_data.get("title", "").strip()
    description = form_data.get("description", "").strip()
    priority = int(form_data.get("priority", 1))
    complete = form_data.get("complete", "false").lower() == "true"

    user = await get_current_user(request.cookies.get("access_token"))
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    new_todo = Todos(
        title=title,
        description=description,
        priority=priority,
        complete=complete,
        owner_id=user.get("id"),
    )
    db.add(new_todo)
    db.commit()
    return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/todo/{todo_id}/update", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    request: Request,
    todo_id: int,
    title: str = Form(...),
    description: str = Form(...),
    priority: int = Form(...),
    complete: bool = Form(False),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request.cookies.get("access_token"))
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    owner_id = int(user.get("id"))
    todo_model = db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == owner_id).first()
    if not todo_model:
        raise HTTPException(status_code=404, detail="Todo Not Found")
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.complete = complete
    db.add(todo_model)
    db.commit()
    return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_303_SEE_OTHER)



@router.delete("/todos/todo/delete/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.post("/todos/todo/delete/{todo_id}")  # Allow POST as an alternative
async def delete_todo(
    request: Request,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    todo_id: int = Path(gt=0)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    todo_model = db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == user.get("id")).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo Not Found.")

    db.delete(todo_model)
    db.commit()

    return RedirectResponse(url="/todos/todo-page", status_code=303)
# @router.delete("/todo/delete/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_todo(
#     user: dict = Depends(get_current_user),
#     db: Session = Depends(get_db),
#     todo_id: int = Path(gt=0)
# ):
#     if user is None:
#         raise HTTPException(status_code=401, detail="Authentication Failed")

#     todo_model = db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == user.get("id")).first()

#     if todo_model is None:
#         raise HTTPException(status_code=404, detail="Todo Not Found.")

#     db.delete(todo_model)
#     db.commit()

#     return RedirectResponse(url="/todos/todo-page", status_code=303)  # Redirect after deletion


