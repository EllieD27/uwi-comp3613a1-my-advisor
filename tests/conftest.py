import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app
from app.models.academic import (
    Advisor,
    Course,
    CoursePrerequisite,
    Program,
    Student,
)
from app.models.user import User
from app.utilities.security import encrypt_password


def _seed(session: Session) -> None:
    student_user = User(
        username="student",
        email="student@example.com",
        password=encrypt_password("studentpass"),
        role="regular_user",
    )
    admin_user = User(
        username="admin",
        email="admin@example.com",
        password=encrypt_password("adminpass"),
        role="admin",
    )
    session.add_all([student_user, admin_user])
    session.commit()
    session.refresh(student_user)
    session.refresh(admin_user)

    program = Program(
        name="Computer Science",
        degree_title="Bachelor of Science",
        required_credits=93,
        max_credits=15,
    )
    advisor = Advisor(
        user_id=admin_user.id,
        name="Admin Advisor",
        email="admin-advisor@example.com",
    )
    other_advisor = Advisor(name="Other Advisor", email="other-advisor@example.com")
    session.add_all([program, advisor, other_advisor])
    session.commit()
    for obj in (program, advisor, other_advisor):
        session.refresh(obj)

    session.add_all(
        [
            Student(
                user_id=student_user.id,
                program_id=program.program_id,
                advisor_id=advisor.advisor_id,
                name="Test Student",
                email="student@example.com",
            ),
            # Belongs to a different advisor and has no login.
            Student(
                program_id=program.program_id,
                advisor_id=other_advisor.advisor_id,
                name="Other Student",
                email="other-student@example.com",
            ),
        ]
    )

    courses = [
        Course(code="COMP 3603", title="Human-Computer Interaction", credits=3,
               faculty="Science and Technology", department="Computing"),
        Course(code="COMP 3605", title="Advanced Computing II", credits=3,
               faculty="Science and Technology", department="Computing"),
        Course(code="MATH 2250", title="Discrete Mathematics", credits=3,
               faculty="Science and Technology", department="Mathematics"),
    ]
    session.add_all(courses)
    session.commit()
    for course in courses:
        session.refresh(course)
    _, advanced, maths = courses

    session.add(CoursePrerequisite(course_id=advanced.course_id, prereq_id=maths.course_id))
    session.commit()


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        _seed(session)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(engine):
    def override_get_session():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()