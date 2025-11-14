from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    roll_number: str
    hostel: Optional[str]
    contact_number: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    roll_number: str = Field(min_length=3, max_length=64)
    hostel: Optional[str] = Field(default=None, max_length=128)
    contact_number: str = Field(min_length=7, max_length=32)


class UserRead(UserBase):
    pass


class UserSummary(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    contact_number: str

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    hostel: Optional[str] = Field(default=None, max_length=128)
    contact_number: Optional[str] = Field(default=None, min_length=7, max_length=32)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


