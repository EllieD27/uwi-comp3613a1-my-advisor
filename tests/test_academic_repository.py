from sqlmodel import Session, SQLModel, create_engine

from app.models.academic import Course, GradeScale, Student, StudentCourse
from app.repositories.academic import AcademicRepository


def test_passed_course_ids_requires_completed_c_or_better():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(
            [
                GradeScale(grade="C", points=2.0),
                GradeScale(grade="B", points=3.0),
                GradeScale(grade="F", points=1.7),
                Student(student_id=1, name="Test Student", email="test@example.com"),
                Course(course_id=1, code="COMP 1601", title="Programming I", credits=3, faculty="COMP", department="Science"),
                Course(course_id=2, code="COMP 1602", title="Programming II", credits=3, faculty="COMP", department="Science"),
                Course(course_id=3, code="COMP 1603", title="Programming III", credits=3, faculty="COMP", department="Science"),
            ]
        )
        session.commit()
        session.add_all(
            [
                StudentCourse(student_id=1, course_id=1, grade="C", status="Completed"),
                StudentCourse(student_id=1, course_id=2, grade="F", status="Completed"),
                StudentCourse(student_id=1, course_id=3, grade="B", status="In progress"),
            ]
        )
        session.commit()

        passed_ids = AcademicRepository(session).get_passed_course_ids(1)

    assert passed_ids == {1}
