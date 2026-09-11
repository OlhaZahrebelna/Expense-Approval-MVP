from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai_service import analyze_expense
from app.auth import get_current_user
from app.database import get_db
from app.models import Category, Expense, ExpenseStatus, User
from app.schemas import (
    CategoryResponse,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseDetailResponse,
    RejectRequest,
)



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
    
    if not current_user.is_employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can create expenses",
        )

    
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

   
    expense = Expense(
        employee_id=current_user.id,
        category_id=category.id,
        approver_id=category.approver_id,
        amount=expense_data.amount,
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
    "/categories",
    response_model=list[CategoryResponse],
)
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    categories = (
        db.query(Category)
        .order_by(Category.name.asc())
        .all()
    )

    return categories


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
    "/queue",
    response_model=list[ExpenseResponse],
)
def get_approval_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_approver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only approvers can view approval queue",
        )

    expenses = (
        db.query(Expense)
        .filter(
            Expense.approver_id == current_user.id,
            Expense.status == ExpenseStatus.PENDING,
        )
        .order_by(Expense.created_at.desc())
        .all()
    )

    return expenses

@router.get(
    "/{expense_id}",
    response_model=ExpenseDetailResponse,
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

    if (
        expense.employee_id != current_user.id
        and expense.approver_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this expense",
        )

    ai_analysis = None

    if expense.approver_id == current_user.id:
        try:
            ai_analysis = analyze_expense(
                amount=expense.amount,
                category_name=expense.category.name,
                description=expense.description,
            )
        except Exception:
            ai_analysis = None

    return {
        "id": expense.id,
        "employee_id": expense.employee_id,
        "category_id": expense.category_id,
        "approver_id": expense.approver_id,
        "amount": expense.amount,
        "description": expense.description,
        "expense_date": expense.expense_date,
        "payment_details": expense.payment_details,
        "status": expense.status,
        "rejection_comment": expense.rejection_comment,
        "created_at": expense.created_at,
        "updated_at": expense.updated_at,
        "ai_analysis": ai_analysis,
    }


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

@router.post(
    "/{expense_id}/approve",
    response_model=ExpenseResponse,
)
def approve_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_approver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only approvers can approve expenses",
        )

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

    if expense.approver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this expense",
        )

    if expense.status != ExpenseStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending expenses can be approved",
        )

    expense.status = ExpenseStatus.APPROVED

    db.commit()
    db.refresh(expense)

    return expense

@router.post(
    "/{expense_id}/reject",
    response_model=ExpenseResponse,
)
def reject_expense(
    expense_id: int,
    reject_data: RejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_approver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only approvers can reject expenses",
        )

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

    if expense.approver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this expense",
        )

    if expense.status != ExpenseStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending expenses can be rejected",
        )

    expense.status = ExpenseStatus.REJECTED
    expense.rejection_comment = reject_data.comment

    db.commit()
    db.refresh(expense)

    return expense

