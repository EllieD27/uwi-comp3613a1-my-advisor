from datetime import datetime
from types import SimpleNamespace

from app.services.semester_plan import SemesterPlanService


class PlansRepository:
    def __init__(self):
        self.student = SimpleNamespace(student_id=7, user_id=42)
        self.plans = [
            SimpleNamespace(
                sp_id=11,
                student_id=7,
                semester="2026/2027 Semester 1",
                created_at=datetime(2026, 8, 1),
                submitted_at=datetime(2026, 8, 3),
                status="Submitted",
            )
        ]
        self.courses = {
            3: SimpleNamespace(course_id=3, code="COMP 3603", title="Human-Computer Interaction", credits=3),
            5: SimpleNamespace(course_id=5, code="INFO 2605", title="Information Systems Elective I", credits=3),
        }
        self.feedback = [
            SimpleNamespace(decision="Request changes", comment="Please add one more course.")
        ]

    def get_student_by_user_id(self, user_id):
        return self.student if user_id == self.student.user_id else None

    def get_student_plans(self, student_id):
        assert student_id == self.student.student_id
        return self.plans

    def get_plan_courses(self, sp_id):
        assert sp_id == 11
        return [SimpleNamespace(course_id=3), SimpleNamespace(course_id=5)]

    def get_course(self, course_id):
        return self.courses.get(course_id)

    def get_feedback_for_plan(self, sp_id):
        assert sp_id == 11
        return self.feedback


def test_my_plans_view_includes_erd_related_courses_and_feedback():
    service = SemesterPlanService(PlansRepository())

    result = service.get_my_plans_view(42)

    assert result["student"].student_id == 7
    assert len(result["plans"]) == 1
    plan_view = result["plans"][0]
    assert plan_view["plan"].status == "Submitted"
    assert [course.code for course in plan_view["courses"]] == ["COMP 3603", "INFO 2605"]
    assert plan_view["total_credits"] == 6
    assert plan_view["feedback"][0].decision == "Request changes"


def test_my_plans_view_is_empty_for_user_without_student_record():
    repo = PlansRepository()
    repo.get_student_by_user_id = lambda user_id: None

    result = SemesterPlanService(repo).get_my_plans_view(999)

    assert result == {"student": None, "plans": []}
