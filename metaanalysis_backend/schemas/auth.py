from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: str = ""
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    avatar_url: str
    storage_used: int
    storage_limit: int
    status: str
    created_at: str

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    user: UserOut
