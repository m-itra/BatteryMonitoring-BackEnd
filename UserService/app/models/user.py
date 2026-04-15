from typing import Annotated

from pydantic import BaseModel, EmailStr, StringConstraints, field_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
RegisterPassword = Annotated[str, StringConstraints(min_length=8)]
LoginPassword = Annotated[str, StringConstraints(min_length=1)]


class RegisterRequest(BaseModel):
    email: EmailStr
    name: NonEmptyStr
    password: RegisterPassword

    @field_validator("password")
    @classmethod
    def password_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password must not be blank")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: LoginPassword

    @field_validator("password")
    @classmethod
    def password_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password must not be blank")
        return value


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
