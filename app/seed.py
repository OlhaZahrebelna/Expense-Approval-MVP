from app.auth import hash_password
from app.database import SessionLocal
from app.models import Category, User


def get_or_create_user(
    db,
    name: str,
    email: str,
    password: str,
):
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user:
        user.is_approver = True
        return user

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        is_employee=True,
        is_approver=True,
    )

    db.add(user)
    db.flush()

    return user


def get_or_create_category(
    db,
    name: str,
    approver_id: int,
):
    category = (
        db.query(Category)
        .filter(Category.name == name)
        .first()
    )

    if category:
        category.approver_id = approver_id
        return category

    category = Category(
        name=name,
        approver_id=approver_id,
    )

    db.add(category)

    return category


def seed():
    db = SessionLocal()

    try:
        finance_approver = get_or_create_user(
            db,
            name="Finance Approver",
            email="finance@test.com",
            password="Finance12345",
        )

        travel_approver = get_or_create_user(
            db,
            name="Travel Approver",
            email="travel@test.com",
            password="Travel12345",
        )

        db.flush()

        get_or_create_category(
            db,
            "Office",
            finance_approver.id,
        )

        get_or_create_category(
            db,
            "Software / Subscriptions",
            finance_approver.id,
        )

        get_or_create_category(
            db,
            "Other",
            finance_approver.id,
        )

        get_or_create_category(
            db,
            "Travel",
            travel_approver.id,
        )

        get_or_create_category(
            db,
            "Client Entertainment",
            travel_approver.id,
        )

        db.commit()

        print("Seed completed successfully.")

        print(
            f"Finance approver: "
            f"{finance_approver.email}, id={finance_approver.id}"
        )

        print(
            f"Travel approver: "
            f"{travel_approver.email}, id={travel_approver.id}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()