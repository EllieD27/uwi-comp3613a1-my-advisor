from __future__ import annotations

from typing import Optional

from sqlmodel import Session, func, select

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


class AcademicRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_student_by_user_id(self, user_id: int) -> Optional[Student]:
        return self.db.exec(select(Student).where(Student.user_id == user_id)).one_or_none()

    def get_student_by_id(self, student_id: int) -> Optional[Student]:
        return self.db.get(Student, student_id)

    def get_students_for_advisor(self, advisor_id: int) -> list[Student]:
        return self.db.exec(
            select(Student)
            .where(Student.advisor_id == advisor_id)
            .order_by(Student.name)
        ).all()

    def get_program(self, program_id: int) -> Optional[Program]:
        return self.db.get(Program, program_id)

    def get_advisor(self, advisor_id: int) -> Optional[Advisor]:
        return self.db.get(Advisor, advisor_id)

    def get_advisor_by_user_id(self, user_id: int) -> Optional[Advisor]:
        return self.db.exec(
            select(Advisor).where(Advisor.user_id == user_id)
        ).one_or_none()

    def get_student_courses(self, student_id: int) -> list[StudentCourse]:
        return self.db.exec(select(StudentCourse).where(StudentCourse.student_id == student_id)).all()

    def get_passed_course_ids(self, student_id: int) -> set[int]:
        passing_grade = self.get_grade_scale("C")
        if passing_grade is None:
            return set()

        statement = (
            select(StudentCourse.course_id)
            .join(GradeScale, StudentCourse.grade == GradeScale.grade)
            .where(
                StudentCourse.student_id == student_id,
                func.lower(StudentCourse.status) == "completed",
                GradeScale.points >= passing_grade.points,
            )
        )
        return set(self.db.exec(statement).all())

    def get_grade_scale(self, grade: str) -> Optional[GradeScale]:
        if not grade:
            return None
        return self.db.get(GradeScale, grade)

    def get_student_plans(self, student_id: int) -> list[SemesterPlan]:
        return self.db.exec(
            select(SemesterPlan)
            .where(SemesterPlan.student_id == student_id)
            .order_by(SemesterPlan.created_at.desc())
        ).all()

    def get_submitted_plans_for_advisor(self, advisor_id: int) -> list[SemesterPlan]:
        return self.db.exec(
            select(SemesterPlan)
            .join(Student, SemesterPlan.student_id == Student.student_id)
            .where(
                Student.advisor_id == advisor_id,
                SemesterPlan.status == "Submitted",
            )
            .order_by(SemesterPlan.submitted_at, SemesterPlan.created_at)
        ).all()

    def get_submitted_plan_for_advisor(
        self,
        advisor_id: int,
        sp_id: int,
    ) -> Optional[SemesterPlan]:
        return self.db.exec(
            select(SemesterPlan)
            .join(Student, SemesterPlan.student_id == Student.student_id)
            .where(
                Student.advisor_id == advisor_id,
                SemesterPlan.sp_id == sp_id,
                SemesterPlan.status == "Submitted",
            )
        ).one_or_none()

    def get_feedback_for_advisor_plan(self, advisor_id: int, sp_id: int) -> Optional[Feedback]:
        return self.db.exec(
            select(Feedback)
            .where(
                Feedback.advisor_id == advisor_id,
                Feedback.sp_id == sp_id,
            )
            .order_by(Feedback.created_at.desc())
        ).first()

    def save_feedback(self, feedback: Feedback) -> Feedback:
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def save_semester_plan(self, plan: SemesterPlan) -> SemesterPlan:
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_feedback_for_plan(self, sp_id: int) -> list[Feedback]:
        return self.db.exec(
            select(Feedback)
            .where(Feedback.sp_id == sp_id)
            .order_by(Feedback.created_at.desc())
        ).all()

    def get_program_requirements(self, program_id: int) -> list[ProgramRequirement]:
        return self.db.exec(
            select(ProgramRequirement).where(ProgramRequirement.program_id == program_id)
        ).all()

    def get_plan_courses(self, sp_id: int) -> list[SemesterPlanCourse]:
        return self.db.exec(
            select(SemesterPlanCourse).where(SemesterPlanCourse.sp_id == sp_id)
        ).all()

    def get_plan_course(self, sp_id: int, course_id: int) -> Optional[SemesterPlanCourse]:
        return self.db.exec(
            select(SemesterPlanCourse).where(
                SemesterPlanCourse.sp_id == sp_id,
                SemesterPlanCourse.course_id == course_id,
            )
        ).one_or_none()

    def get_courses_by_codes(self, course_codes: list[str]) -> list[Course]:
        if not course_codes:
            return []
        return self.db.exec(select(Course).where(Course.code.in_(course_codes))).all()

    def get_course_prerequisites(self, course_id: int) -> list[CoursePrerequisite]:
        return self.db.exec(
            select(CoursePrerequisite).where(CoursePrerequisite.course_id == course_id)
        ).all()

    def get_course_by_code(self, code: str) -> Optional[Course]:
        return self.db.exec(select(Course).where(Course.code == code)).one_or_none()

    def get_course(self, course_id: int) -> Optional[Course]:
        return self.db.get(Course, course_id)

    def get_all_programs(self) -> list[Program]:
        return self.db.exec(select(Program)).all()
