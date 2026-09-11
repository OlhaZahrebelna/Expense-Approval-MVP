from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Category, Expense, ExpenseStatus, User
from app.schemas import ExpenseCreate, ExpenseResponse


router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"],
)


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Check that the current user can create expenses
    if not current_user.is_employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can create expenses",
        )

    # 2. Find the selected category
    category = (
        db.query(Category)
        .filter(Category.id == expense_data.category_id)
        .first()
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # 3. Create expense
    expense = Expense(
        employee_id=current_user.id,
        category_id=category.id,
        approver_id=category.approver_id,
        amount=float(expense_data.amount),
        description=expense_data.description,
        expense_date=expense_data.expense_date,
        payment_details=expense_data.payment_details,
        status=ExpenseStatus.PENDING,
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    return expense


@router.get(
    "/my",
    response_model=list[ExpenseResponse],
)
def get_my_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expenses = (
        db.query(Expense)
        .filter(Expense.employee_id == current_user.id)
        .order_by(Expense.created_at.desc())
        .all()
    )

    return expenses


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id)
        .first()
    )

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    # Employee who created it OR assigned approver may see it
    if (
        expense.employee_id != current_user.id
        and expense.approver_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this expense",
        )

    return expense


@router.post(
    "/{expense_id}/withdraw",
    response_model=ExpenseResponse,
)
def withdraw_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id)
        .first()
    )

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    # Only the employee who created the expense may withdraw it
    if expense.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can withdraw only your own expense",
        )

    # Only pending expenses can be withdrawn
    if expense.status != ExpenseStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending expenses can be withdrawn",
        )

    expense.status = ExpenseStatus.WITHDRAWN

    db.commit()
    db.refresh(expense)

    return expense
