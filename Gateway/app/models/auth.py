from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, field_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
RegisterPassword = Annotated[str, StringConstraints(min_length=8)]
LoginPassword = Annotated[str, StringConstraints(min_length=1)]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "password": "password123"
            }
        }
    )

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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }
    )

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


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
