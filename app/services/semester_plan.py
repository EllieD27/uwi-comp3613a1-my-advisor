from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session

from app.models.academic import SemesterPlan, SemesterPlanCourse


class SemesterPlanService:
    AVAILABLE_CODES = tuple(sorted((
        "ACCT 1002", "ACCT 1003",
        "COMP 1600", "COMP 1601", "COMP 1602", "COMP 1603",
        "COMP 2601", "COMP 2602", "COMP 2603", "COMP 2604", "COMP 2605", "COMP 2606", "COMP 2611",
        "COMP 3603", "COMP 3606", "COMP 3613",
        "ECON 1001", "ECON 1002",
        "FOUN 1101", "FOUN 1105", "FOUN 1301",
        "INFO 3609",
        "MGMT 2008", "MGMT 2021", "MGMT 2032",
        "MKTG 2001",
    )))
    MAX_CREDITS = 15

    def __init__(self, academic_repo):
        self.academic_repo = academic_repo

    def _group_for_code(self, code: str) -> str:
        return code.split(maxsplit=1)[0]

    def _course_by_code(self, code: str):
        return self.academic_repo.get_course_by_code(code)

    def _max_credits_for_student(self, student) -> int:
        program = (
            self.academic_repo.get_program(student.program_id)
            if student.program_id
            else None
        )
        if program is not None and program.max_credits > 0:
            return program.max_credits
        return self.MAX_CREDITS

    def _plan_total_credits(self, sp_id: int) -> int:
        total = 0
        for entry in self.academic_repo.get_plan_courses(sp_id):
            course = self.academic_repo.get_course(entry.course_id)
            if course is not None:
                total += course.credits
        return total

    def get_my_plans_view(self, user_id: int) -> dict[str, Any]:
        student = self.academic_repo.get_student_by_user_id(user_id)
        if student is None:
            return {"student": None, "plans": []}

        plans = []
        for plan in self.academic_repo.get_student_plans(student.student_id):
            courses = []
            for entry in self.academic_repo.get_plan_courses(plan.sp_id):
                course = self.academic_repo.get_course(entry.course_id)
                if course is not None:
                    courses.append(course)

            plans.append({
                "plan": plan,
                "courses": courses,
                "total_credits": sum(course.credits for course in courses),
                "feedback": self.academic_repo.get_feedback_for_plan(plan.sp_id),
            })

        return {"student": student, "plans": plans}

    def _passed_course_ids(self, student_id: int) -> set[int]:
        return self.academic_repo.get_passed_course_ids(student_id)

    def _completed_course_ids(self, student_id: int) -> set[int]:
        return {
            item.course_id
            for item in self.academic_repo.get_student_courses(student_id)
            if item.status and item.status.strip().casefold() == "completed"
        }

    def _plan_for_student(self, student_id: int):
        plans = self.academic_repo.get_student_plans(student_id)
        if plans:
            return plans[0]
        plan = SemesterPlan(
            student_id=student_id,
            semester="2026/2027 Semester 1",
            status="Draft",
            notes="Ready for advisor feedback",
        )
        self.academic_repo.db.add(plan)
        self.academic_repo.db.commit()
        self.academic_repo.db.refresh(plan)
        return plan

    def _is_prerequisite_missing(self, course_id: int, completed_ids: set[int]) -> bool:
        prerequisites = self.academic_repo.get_course_prerequisites(course_id)
        if not prerequisites:
            return False
        return not any(item.prereq_id in completed_ids for item in prerequisites)

    def get_build_plan_view(self, user_id: int) -> dict[str, Any]:
        student = self.academic_repo.get_student_by_user_id(user_id)
        if student is None:
            return {
                "student": None,
                "semester": "Not selected",
                "plan": None,
                "selected_codes": [],
                "selected_courses": [],
                "available_courses": [],
                "plan_total_credits": 0,
                "max_credits": self.MAX_CREDITS,
                "checks_passed": False,
            }

        plan = self._plan_for_student(student.student_id)
        max_credits = self._max_credits_for_student(student)
        passed_course_ids = self._passed_course_ids(student.student_id)
        completed_course_ids = self._completed_course_ids(student.student_id)
        selected_codes: list[str] = []
        selected_course_rows: list[dict[str, Any]] = []
        for plan_entry in self.academic_repo.get_plan_courses(plan.sp_id):
            course = self.academic_repo.get_course(plan_entry.course_id)
            if course is None:
                continue
            selected_codes.append(course.code)
            selected_course_rows.append({
                "course": course,
                "course_id": course.course_id,
                "code": course.code,
                "credits": course.credits,
            })

        plan_total_credits = sum(item["credits"] for item in selected_course_rows)
        available_course_rows: list[dict[str, Any]] = []
        for code in self.AVAILABLE_CODES:
            course = self._course_by_code(code)
            if course is None:
                continue
            if code in selected_codes:
                status = "Added"
            elif course.course_id in completed_course_ids:
                status = "Completed"
            elif self._is_prerequisite_missing(course.course_id, passed_course_ids):
                status = "Needs MATH 2250" if code == "COMP 3605" else "Needs prerequisite"
            elif plan_total_credits + course.credits > max_credits:
                status = "Max credits reached"
            else:
                status = "Add"
            available_course_rows.append({
                "code": course.code,
                "title": course.title,
                "credits": course.credits,
                "group": self._group_for_code(code),
                "status": status,
            })

        checks_passed = (
            plan_total_credits <= max_credits
            and all(
                not self._is_prerequisite_missing(
                    self._course_by_code(code).course_id,
                    passed_course_ids,
                )
                for code in selected_codes
                if self._course_by_code(code) is not None
            )
        )

        return {
            "student": student,
            "semester": plan.semester,
            "plan": plan,
            "selected_codes": selected_codes,
            "selected_courses": selected_course_rows,
            "available_courses": available_course_rows,
            "plan_total_credits": plan_total_credits,
            "max_credits": max_credits,
            "checks_passed": checks_passed,
        }

    def add_course_to_plan(self, user_id: int, course_code: str) -> bool:
        student = self.academic_repo.get_student_by_user_id(user_id)
        if student is None:
            return False
        plan = self._plan_for_student(student.student_id)
        course = self._course_by_code(course_code)
        if course is None or course_code not in self.AVAILABLE_CODES:
            return False
        if self.academic_repo.get_plan_course(plan.sp_id, course.course_id):
            return False
        if course.course_id in self._completed_course_ids(student.student_id):
            return False
        if self._is_prerequisite_missing(
            course.course_id,
            self._passed_course_ids(student.student_id),
        ):
            return False
        if self._plan_total_credits(plan.sp_id) + course.credits > self._max_credits_for_student(student):
            return False
        self.academic_repo.db.add(
            SemesterPlanCourse(sp_id=plan.sp_id, course_id=course.course_id)
        )
        self.academic_repo.db.commit()
        return True

    def remove_course_from_plan(self, user_id: int, course_code: str) -> bool:
        student = self.academic_repo.get_student_by_user_id(user_id)
        if student is None:
            return False
        plan = self._plan_for_student(student.student_id)
        course = self._course_by_code(course_code)
        if course is None:
            return False
        plan_course = self.academic_repo.get_plan_course(plan.sp_id, course.course_id)
        if plan_course is None:
            return False
        self.academic_repo.db.delete(plan_course)
        self.academic_repo.db.commit()
        return True

    def submit_plan(self, user_id: int) -> bool:
        student = self.academic_repo.get_student_by_user_id(user_id)
        if student is None:
            return False
        plan = self._plan_for_student(student.student_id)
        plan.status = "Submitted"
        plan.submitted_at = datetime.now(timezone.utc)
        self.academic_repo.db.add(plan)
        self.academic_repo.db.commit()
        return True
