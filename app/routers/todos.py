from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Path, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routers.auth import get_current_user
from app.schemas import schemas
from app.models import models


router = APIRouter(prefix='/todos', tags=["User Todos Routes"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


templates = Jinja2Templates(directory="app/templates")


def redirect_to_login():
    redirect_response = RedirectResponse(url='/auth/login-page', status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key='access_token')
    return redirect_response


### Pages
@router.get('/todo-page')
async def render_todos_page(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        todos = db.query(models.Todos).filter(models.Todos.owner_id == user.get('id')).all()
        return templates.TemplateResponse('todos.html', {'request': request, 'todos': todos, 'user': user})
    except:
        return redirect_to_login()



@router.get('/add-todo-page')
async def render_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})

    except:
        return redirect_to_login()


@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

        return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})

    except:
        return redirect_to_login()



### Endopoints

@router.get("/", response_model=list[schemas.Todo], status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    return db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(
    user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    db_todos = (
        db.query(models.Todos)
        .filter(models.Todos.id == todo_id)
        .filter(models.Todos.owner_id == user.get("id"))
        .first()
    )
    if db_todos is not None:
        return db_todos
    raise HTTPException(status_code=404, detail="Todo not found.")


@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(
    user: user_dependency, db: db_dependency, todo_request: schemas.TodoRequest
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    db_todo = models.Todos(**todo_request.model_dump(), owner_id=user.get("id"))

    db.add(db_todo)
    db.commit()


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    user: user_dependency,
    db: db_dependency,
    todo_request: schemas.TodoRequest,
    todo_id: int = Path(gt=0),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    db_todo = (
        db.query(models.Todos)
        .filter(models.Todos.id == todo_id)
        .filter(models.Todos.owner_id == user.get("id"))
        .first()
    )
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found.")

    db_todo.title = todo_request.title
    db_todo.description = todo_request.description
    db_todo.priority = todo_request.priority
    db_todo.complete = todo_request.complete

    db.add(db_todo)
    db.commit()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    db_todo = (
        db.query(models.Todos)
        .filter(models.Todos.id == todo_id)
        .filter(models.Todos.owner_id == user.get("id"))
        .first()
    )
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found.")
    db.query(models.Todos).filter(models.Todos.id == todo_id).filter(
        models.Todos.owner_id == user.get("id")
    ).delete()
    db.commit()
