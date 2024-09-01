from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Path
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.routers.auth import get_current_user
from app.schemas import schemas
from app.models import models


router = APIRouter(prefix="/admin", tags=["Admin Routes"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/todos", response_model=list[schemas.Todo], status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency, user: user_dependency):
    if user is None or user.get("user_role") != "admin":
        raise HTTPException(status_code=401, detail="Authentication Failed")
    db_todos = db.query(models.Todos).all()
    return db_todos


@router.delete("/todos/delete-todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)
):
    if user is None or user.get("user_role") != "admin":
        raise HTTPException(status_code=401, detail="Authentication Failed")
    db_todo = db.query(models.Todos).filter_by(id=todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found.")
    db.delete(db_todo)
    db.commit()
