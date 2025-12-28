from pydantic import BaseModel, EmailStr, ConfigDict

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
    name: str
    password: str


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
    password: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse