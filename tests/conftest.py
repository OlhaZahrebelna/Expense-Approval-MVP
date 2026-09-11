import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Category, User
from app.auth import hash_password


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    yield db

    db.close()


@pytest.fixture()
def client(db):
    return TestClient(app)


@pytest.fixture()
def test_users(db):
    employee = User(
        name="Employee",
        email="employee@test.com",
        hashed_password=hash_password("Employee123"),
        is_employee=True,
        is_approver=False,
    )

    other_employee = User(
        name="Other Employee",
        email="other_employee@test.com",
        hashed_password=hash_password("OtherEmployee123"),
        is_employee=True,
        is_approver=False,
    )
    
    finance_approver = User(
        name="Finance Approver",
        email="finance@test.com",
        hashed_password=hash_password("Finance123"),
        is_employee=True,
        is_approver=True,
    )

    travel_approver = User(
        name="Travel Approver",
        email="travel@test.com",
        hashed_password=hash_password("Travel123"),
        is_employee=True,
        is_approver=True,
    )


    db.add_all([
        employee,
        other_employee,
        finance_approver,
        travel_approver,
    ])

    db.flush()

    office = Category(
        name="Office",
        approver_id=finance_approver.id,
    )

    travel = Category(
        name="Travel",
        approver_id=travel_approver.id,
    )

    db.add_all([office, travel])

    db.commit()

    return {
        "employee": employee,
        "other_employee": other_employee,
        "finance_approver": finance_approver,
        "travel_approver": travel_approver,
        "office": office,
        "travel": travel,
    }
