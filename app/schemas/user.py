from pydantic import BaseModel


class UserRead(BaseModel):
    email: str
    name: str


class UserCreate(BaseModel):
    email: str
    password: str
    name: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
