from types import SimpleNamespace

from app.services.degree_progress import DegreeProgressService


CORE_CODES = (
    "ACCT 1002", "ACCT 1003", "COMP 1600", "COMP 1601", "COMP 1602",
    "COMP 1603", "COMP 2601", "COMP 2602", "COMP 2603", "COMP 2604",
    "COMP 2605", "COMP 2606", "COMP 2611", "ECON 1001", "ECON 1002",
    "FOUN 1101", "FOUN 1105", "FOUN 1301", "INFO 3609", "MKTG 2001",
    "MGMT 2021", "MGMT 2008", "MGMT 2032",
)
ELECTIVE_CODES = (
    "COMP 3603", "COMP 3605", "COMP 3606", "COMP 3613",
    "INFO 2605", "INFO 3606", "MATH 2250", "MGMT 2012",
)


class DegreeProgressRepository:
    def __init__(self):
        codes = CORE_CODES + ELECTIVE_CODES
        self.courses = {
            index: SimpleNamespace(
                course_id=index,
                code=code,
                title=code,
                credits=3,
            )
            for index, code in enumerate(codes, start=1)
        }
        self.course_ids = {course.code: course.course_id for course in self.courses.values()}
        self.student = SimpleNamespace(student_id=1, user_id=10, program_id=2, advisor_id=3)
        self.program = SimpleNamespace(program_id=2, required_credits=93)
        self.requirements = [
            SimpleNamespace(
                course_id=self.course_ids[code],
                category="Foundation" if code == "FOUN 1101" else "Core",
            )
            for code in CORE_CODES
        ] + [
            SimpleNamespace(course_id=self.course_ids[code], category="Electives")
            for code in ELECTIVE_CODES
        ]
        self.student_courses = [
            SimpleNamespace(course_id=self.course_ids[code], grade="B", status="Completed", sem_completed="2024/2025")
            for code in CORE_CODES
        ]

    def get_student_by_user_id(self, user_id):
        return self.student if user_id == 10 else None

    def get_program(self, program_id):
        return self.program

    def get_advisor(self, advisor_id):
        return SimpleNamespace(advisor_id=advisor_id)

    def get_student_courses(self, student_id):
        return self.student_courses

    def get_course(self, course_id):
        return self.courses.get(course_id)

    def get_program_requirements(self, program_id):
        return self.requirements

    def get_student_plans(self, student_id):
        return []

    def get_passed_course_ids(self, student_id):
        return {item.course_id for item in self.student_courses}

    def get_courses_by_codes(self, codes):
        return []

    def get_course_prerequisites(self, course_id):
        return []

    def get_grade_scale(self, grade):
        return SimpleNamespace(grade=grade, points=3.0)


def test_dashboard_credit_and_course_count_cards_reconcile_to_93_credits():
    result = DegreeProgressService(DegreeProgressRepository()).get_student_progress(10)

    assert len(CORE_CODES) == 23
    assert len(ELECTIVE_CODES) == 8
    assert result["earned_credits"] == 69
    assert result["required_credits"] == 93
    assert result["core_earned_courses"] == 23
    assert result["core_required_courses"] == 23
    assert result["elective_earned_courses"] == 0
    assert result["elective_required_courses"] == 8
