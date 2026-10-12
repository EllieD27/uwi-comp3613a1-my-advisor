from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel


class Program(SQLModel, table=True):
    __tablename__ = "program"

    program_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    degree_title: str
    required_credits: int = 0
    max_credits: int = 0


class Advisor(SQLModel, table=True):
    __tablename__ = "advisor"

    advisor_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", unique=True, index=True)
    name: str
    email: str = Field(index=True)


class Student(SQLModel, table=True):
    __tablename__ = "student"

    student_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", unique=True, index=True)
    program_id: Optional[int] = Field(default=None, foreign_key="program.program_id", index=True)
    advisor_id: Optional[int] = Field(default=None, foreign_key="advisor.advisor_id", index=True)
    name: str
    email: str = Field(index=True)
    status: str = "active"


class Course(SQLModel, table=True):
    __tablename__ = "course"

    course_id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    title: str
    credits: int
    faculty: str
    department: str


class GradeScale(SQLModel, table=True):
    __tablename__ = "grade_scale"

    grade: str = Field(primary_key=True, index=True)
    points: float


class ProgramRequirement(SQLModel, table=True):
    __tablename__ = "program_requirement"

    pr_id: Optional[int] = Field(default=None, primary_key=True)
    program_id: int = Field(foreign_key="program.program_id", index=True)
    course_id: int = Field(foreign_key="course.course_id", index=True)
    category: str
    required: bool = True
    note: str = ""


class SemesterPlan(SQLModel, table=True):
    __tablename__ = "semester_plan"

    sp_id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id", index=True)
    semester: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    status: str = "Draft"
    notes: str = ""


class SemesterPlanCourse(SQLModel, table=True):
    __tablename__ = "semester_plan_course"

    __table_args__ = (UniqueConstraint("sp_id", "course_id"),)

    spc_id: Optional[int] = Field(default=None, primary_key=True)
    sp_id: int = Field(foreign_key="semester_plan.sp_id", index=True)
    course_id: int = Field(foreign_key="course.course_id", index=True)


class Feedback(SQLModel, table=True):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint(
            "decision IN ('Approve', 'Request changes')",
            name="ck_feedback_decision_allowed",
        ),
    )

    feedback_id: Optional[int] = Field(default=None, primary_key=True)
    sp_id: int = Field(foreign_key="semester_plan.sp_id", index=True)
    advisor_id: int = Field(foreign_key="advisor.advisor_id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    comment: str = ""
    decision: str = "Approve"

class StudentCourse(SQLModel, table=True):
    __tablename__ = "student_course"

    sc_id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id", index=True)
    course_id: int = Field(foreign_key="course.course_id", index=True)
    grade: Optional[str] = Field(default=None, foreign_key="grade_scale.grade", index=True)
    sem_completed: str = ""
    status: str = "Completed"


class CoursePrerequisite(SQLModel, table=True):
    __tablename__ = "course_prerequisite"

    cp_id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.course_id", index=True)
    prereq_id: int = Field(foreign_key="course.course_id", index=True)
