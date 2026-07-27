from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    profile: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class SessionRead(BaseModel):
    authenticated: bool
    profile: str
