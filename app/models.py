import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)

from sqlalchemy.orm import relationship

from app.database import Base


class ExpenseStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    is_employee = Column(Boolean, default=True)
    is_approver = Column(Boolean, default=False)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, unique=True, nullable=False)

    approver_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    approver = relationship("User")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False,
    )

    approver_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    amount = Column(Numeric(12, 2),nullable=False,)

    description = Column(Text, nullable=False)

    expense_date = Column(Date, nullable=False)

    payment_details = Column(Text, nullable=False)

    status = Column(
        Enum(ExpenseStatus),
        default=ExpenseStatus.PENDING,
        nullable=False,
    )

    rejection_comment = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    employee = relationship(
        "User",
        foreign_keys=[employee_id],
    )

    approver = relationship(
        "User",
        foreign_keys=[approver_id],
    )

    category = relationship("Category")
