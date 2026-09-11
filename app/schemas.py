from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import ExpenseStatus


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_employee: bool
    is_approver: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CategoryResponse(BaseModel):
    id: int
    name: str
    approver_id: int

    class Config:
        from_attributes = True


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    category_id: int
    description: str
    expense_date: date
    payment_details: str

    @field_validator("description", "payment_details")
    @classmethod
    def validate_not_empty(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value


class ExpenseResponse(BaseModel):
    id: int
    employee_id: int
    category_id: int
    approver_id: int

    amount: Decimal
    description: str
    expense_date: date
    payment_details: str

    status: ExpenseStatus
    rejection_comment: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AIAnalysis(BaseModel):
    summary: str
    flagged: bool
    reason: Optional[str] = None


class ExpenseDetailResponse(ExpenseResponse):
    ai_analysis: Optional[AIAnalysis] = None


class RejectRequest(BaseModel):
    comment: str

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Rejection comment is required")

        return value
    