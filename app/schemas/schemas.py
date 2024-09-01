from pydantic import BaseModel, Field


class CreateUserBase(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    phone_number: str
    is_active: bool = Field(default=True)


class CreateUserRequest(CreateUserBase):
    password: str


class User(CreateUserBase):
    id: int
    hashed_password: str


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


class Todo(TodoRequest):
    id: int
    owner_id: int


Todo.model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)
