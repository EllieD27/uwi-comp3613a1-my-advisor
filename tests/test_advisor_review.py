from datetime import datetime
from types import SimpleNamespace

from app.services.advisor_review import AdvisorReviewService


class AdvisorRepositoryStub:
    def __init__(self):
        self.advisor = SimpleNamespace(advisor_id=4, user_id=2)
        self.student = SimpleNamespace(
            student_id=9,
            user_id=12,
            name="Nelly miller",
            email="nelly@example.com",
            program_id=3,
        )
        self.plan = SimpleNamespace(
            sp_id=22,
            student_id=9,
            semester="2026/2027 Semester 1",
            submitted_at=datetime(2026, 10, 1),
            status="Submitted",
        )
        self.courses = [
            SimpleNamespace(course_id=31, code="COMP 2601", title="Computer Architecture", credits=3),
            SimpleNamespace(course_id=32, code="COMP 2602", title="Computer Networks", credits=3),
        ]
        self.feedback = None
        self.saved_plans = []
        self.saved_feedback = []

    def get_advisor_by_user_id(self, user_id):
        return self.advisor if user_id == 2 else None

    def get_submitted_plans_for_advisor(self, advisor_id):
        return [self.plan] if advisor_id == self.advisor.advisor_id else []

    def get_student_by_id(self, student_id):
        return self.student if student_id == self.student.student_id else None

    def get_plan_courses(self, sp_id):
        return [SimpleNamespace(course_id=course.course_id) for course in self.courses]

    def get_course(self, course_id):
        return next((course for course in self.courses if course.course_id == course_id), None)

    def get_program(self, program_id):
        return SimpleNamespace(program_id=3, name="BSc Computer Science", degree_title="Bachelor of Science")

    def get_feedback_for_advisor_plan(self, advisor_id, sp_id):
        if advisor_id != self.advisor.advisor_id or sp_id != self.plan.sp_id:
            return None
        return self.feedback

    def get_submitted_plan_for_advisor(self, advisor_id, sp_id):
        if advisor_id == self.advisor.advisor_id and sp_id == self.plan.sp_id and self.plan.status == "Submitted":
            return self.plan
        return None

    def save_feedback(self, feedback):
        self.feedback = feedback
        self.saved_feedback.append(feedback)
        return feedback

    def save_semester_plan(self, plan):
        self.saved_plans.append(plan)
        return plan


def test_admin_dashboard_includes_assigned_pending_plan_and_gpa():
    repo = AdvisorRepositoryStub()
    service = AdvisorReviewService(repo)
    service.degree_progress_service.get_student_progress = lambda user_id: {
        "earned_credits": 6,
        "required_credits": 93,
        "core_earned_courses": 0,
        "core_required_courses": 23,
        "elective_earned_courses": 0,
        "elective_required_courses": 8,
        "gpa": 3.5,
        "completed_courses": [],
    }

    result = service.get_admin_dashboard_view(2)

    assert result["advisor"] is repo.advisor
    assert len(result["pending_plans"]) == 1
    pending = result["pending_plans"][0]
    assert pending["student"] is repo.student
    assert pending["progress"]["gpa"] == 3.5
    assert pending["plan_credits"] == 6
    assert [course.code for course in pending["courses"]] == ["COMP 2601", "COMP 2602"]


def test_submit_plan_decision_saves_feedback_and_updates_plan_status():
    repo = AdvisorRepositoryStub()
    service = AdvisorReviewService(repo)

    assert service.submit_plan_decision(2, 22, "Request changes", "Include the prerequisite course.") is True

    assert repo.plan.status == "Request Changes"
    assert repo.feedback.decision == "Request changes"
    assert repo.feedback.comment == "Include the prerequisite course."
    assert repo.saved_plans == [repo.plan]
    assert len(repo.saved_feedback) == 1


def test_submit_plan_decision_rejects_unassigned_or_invalid_decisions():
    repo = AdvisorRepositoryStub()
    service = AdvisorReviewService(repo)

    assert service.submit_plan_decision(2, 22, "Ignore", "") is False
    assert service.submit_plan_decision(999, 22, "Approve", "Looks good") is False
    assert repo.saved_feedback == []
    assert repo.saved_plans == []
