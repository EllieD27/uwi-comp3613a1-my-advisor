from __future__ import annotations

from typing import Any

from app.repositories.academic import AcademicRepository


class DegreeProgressService:
    YEAR_ONE_CODES = (
        "ACCT 1002",
        "ACCT 1003",
        "COMP 1601",
        "COMP 1602",
        "COMP 1603",
        "ECON 1001",
        "ECON 1002",
        "FOUN 1101",
        "FOUN 1105",
        "FOUN 1301",
    )
    YEAR_TWO_CODES = (
        "COMP 2601",
        "COMP 2602",
        "COMP 2603",
        "COMP 2604",
        "COMP 2605",
        "COMP 2606",
        "COMP 2611",
        "MGMT 2008",
        "MGMT 2021",
        "MGMT 2032",
        "MKTG 2001",
    )
    ELIGIBLE_NEXT_SEMESTER_CODES = (
        "COMP 3603",
        "COMP 3606",
        "COMP 3613",
        "INFO 2605",
        "INFO 3606",
        "MATH 2250",
        "MGMT 2012",
    )

    def __init__(self, academic_repo: AcademicRepository):
        self.academic_repo = academic_repo

    def get_student_gpa(self, user_id: int) -> float | None:
        student = self.academic_repo.get_student_by_user_id(user_id)
        if student is None:
            return None

        total_quality_points = 0.0
        total_credits = 0
        for item in self.academic_repo.get_student_courses(student.student_id):
            if item.status.strip().casefold() != "completed" or not item.grade:
                continue
            course = self.academic_repo.get_course(item.course_id)
            if course is None:
                continue
            grade_scale = self.academic_repo.get_grade_scale(item.grade)
            if grade_scale is None:
                continue
            total_quality_points += course.credits * grade_scale.points
            total_credits += course.credits

        if total_credits == 0:
            return None
        return round(total_quality_points / total_credits, 2)

    def get_student_progress(self, user_id: int) -> dict[str, Any]:
        student = self.academic_repo.get_student_by_user_id(user_id)
        if student is None:
            return {
                "student": None,
                "program": None,
                "completed_courses": [],
                "planned_courses": [],
                "eligible_next_semester": [],
                "required_credits": 0,
                "earned_credits": 0,
                "remaining_credits": 0,
                "completion_percent": 0,
                "requirements": [],
                "core_earned_courses": 0,
                "core_required_courses": 0,
                "elective_earned_courses": 0,
                "elective_required_courses": 0,
                "gpa": None,
                "semester": "Not selected",
            }

        program = self.academic_repo.get_program(student.program_id) if student.program_id else None
        advisor = self.academic_repo.get_advisor(student.advisor_id) if student.advisor_id else None
        if program is None:
            return {
                "student": student,
                "advisor": advisor,
                "program": None,
                "completed_courses": [],
                "planned_courses": [],
                "eligible_next_semester": [],
                "required_credits": 0,
                "earned_credits": 0,
                "remaining_credits": 0,
                "completion_percent": 0,
                "requirements": [],
                "core_earned_courses": 0,
                "core_required_courses": 0,
                "elective_earned_courses": 0,
                "elective_required_courses": 0,
                "gpa": self.get_student_gpa(user_id),
                "semester": "Not selected",
            }

        completed_courses = []
        earned_credits = 0
        completed_course_ids = set()
        for item in self.academic_repo.get_student_courses(student.student_id):
            if item.status.strip().casefold() != "completed":
                continue
            course = self.academic_repo.get_course(item.course_id)
            if course is not None:
                completed_courses.append({
                    "course": course,
                    "grade": item.grade,
                    "status": item.status,
                    "sem_completed": item.sem_completed,
                })
                completed_course_ids.add(course.course_id)
                earned_credits += course.credits

        requirements = []
        program_requirements = self.academic_repo.get_program_requirements(program.program_id)
        for requirement in program_requirements:
            course = self.academic_repo.get_course(requirement.course_id)
            requirements.append({
                "requirement": requirement,
                "course": course,
                "is_complete": course is not None and course.course_id in completed_course_ids,
            })

        core_requirements = [
            item for item in requirements
            if item["requirement"].category.strip().casefold().startswith(("core", "foundation"))
        ]
        elective_requirements = [
            item for item in requirements
            if "elective" in item["requirement"].category.strip().casefold()
        ]
        core_required_courses = sum(
            1 for item in core_requirements if item["course"] is not None
        )
        core_earned_courses = sum(
            1
            for item in core_requirements
            if item["course"] is not None and item["is_complete"]
        )
        elective_required_courses = sum(
            1 for item in elective_requirements if item["course"] is not None
        )
        elective_earned_courses = sum(
            1
            for item in elective_requirements
            if item["course"] is not None and item["is_complete"]
        )

        required_credits = program.required_credits
        remaining = max(required_credits - earned_credits, 0)
        completion_percent = round((earned_credits / required_credits) * 100, 1) if required_credits else 0.0

        plans = self.academic_repo.get_student_plans(student.student_id)
        passed_course_ids = self.academic_repo.get_passed_course_ids(student.student_id)
        completed_year_one_codes = {
            item["course"].code
            for item in completed_courses
            if item["course"].code in self.YEAR_ONE_CODES
        }
        candidate_codes = (
            tuple(code for code in self.YEAR_ONE_CODES if code not in completed_year_one_codes)
            if len(completed_year_one_codes) < len(self.YEAR_ONE_CODES)
            else self.YEAR_TWO_CODES
        )
        if len(completed_year_one_codes) == len(self.YEAR_ONE_CODES):
            candidate_codes = tuple(dict.fromkeys(
                (*candidate_codes, *self.ELIGIBLE_NEXT_SEMESTER_CODES)
            ))
        eligible_candidates = self.academic_repo.get_courses_by_codes(
            list(candidate_codes)
        )
        candidates_by_code = {course.code: course for course in eligible_candidates}
        eligible_next_semester = []
        for course_code in candidate_codes:
            course = candidates_by_code.get(course_code)
            if course is None:
                continue
            if course.course_id in completed_course_ids:
                continue
            prerequisites = self.academic_repo.get_course_prerequisites(course.course_id)
            if (
                course_code not in self.YEAR_TWO_CODES
                and any(item.prereq_id not in passed_course_ids for item in prerequisites)
            ):
                continue
            eligible_next_semester.append({
                "course": course,
                "category": (
                    "Core"
                    if course_code in self.YEAR_ONE_CODES or course_code in self.YEAR_TWO_CODES
                    else "Elective"
                ),
            })

        return {
            "student": student,
            "advisor": advisor,
            "program": program,
            "completed_courses": completed_courses,
            "planned_courses": [],
            "eligible_next_semester": eligible_next_semester,
            "required_credits": required_credits,
            "earned_credits": earned_credits,
            "remaining_credits": remaining,
            "completion_percent": completion_percent,
            "requirements": requirements,
            "core_earned_courses": core_earned_courses,
            "core_required_courses": core_required_courses,
            "elective_earned_courses": elective_earned_courses,
            "elective_required_courses": elective_required_courses,
            "gpa": self.get_student_gpa(user_id),
            "semester": plans[0].semester if plans else "Not selected",
        }
