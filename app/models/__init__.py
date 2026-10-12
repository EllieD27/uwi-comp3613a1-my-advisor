"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.academic import (
    Advisor,
    Course,
    CoursePrerequisite,
    Feedback,
    GradeScale,
    Program,
    ProgramRequirement,
    SemesterPlan,
    SemesterPlanCourse,
    Student,
    StudentCourse,
)
from app.models.user import User

__all__ = [
    "User",
    "Advisor",
    "Course",
    "CoursePrerequisite",
    "Feedback",
    "GradeScale",
    "Program",
    "ProgramRequirement",
    "SemesterPlan",
    "SemesterPlanCourse",
    "Student",
    "StudentCourse",
]
