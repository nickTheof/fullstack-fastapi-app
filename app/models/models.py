from sqlalchemy import Integer, VARCHAR, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(VARCHAR(100), unique=True)
    username: Mapped[str] = mapped_column(VARCHAR(20), unique=True)
    first_name: Mapped[str] = mapped_column(VARCHAR(20))
    last_name: Mapped[str] = mapped_column(VARCHAR(20))
    hashed_password: Mapped[str] = mapped_column(VARCHAR(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(VARCHAR(20))
    phone_number: Mapped[str] = mapped_column(VARCHAR(50))


class Todos(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(VARCHAR(100))
    description: Mapped[str] = mapped_column(VARCHAR(100))
    priority: Mapped[int] = mapped_column(Integer)
    complete: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
