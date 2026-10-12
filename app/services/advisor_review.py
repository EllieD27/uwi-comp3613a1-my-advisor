from __future__ import annotations

from typing import Any

from app.models.academic import Feedback
from app.repositories.academic import AcademicRepository
from app.services.degree_progress import DegreeProgressService


class AdvisorReviewService:
    def __init__(self, academic_repo: AcademicRepository):
        self.academic_repo = academic_repo
        self.degree_progress_service = DegreeProgressService(academic_repo)

    def get_admin_dashboard_view(self, user_id: int) -> dict[str, Any]:
        advisor = self.academic_repo.get_advisor_by_user_id(user_id)
        if advisor is None:
            return {"advisor": None, "pending_plans": []}

        pending_plans = []
        for plan in self.academic_repo.get_submitted_plans_for_advisor(advisor.advisor_id):
            student = self.academic_repo.get_student_by_id(plan.student_id)
            if student is None:
                continue

            degree_progress = self.degree_progress_service.get_student_progress(
                student.user_id
            ) if student.user_id is not None else None
            courses = []
            for plan_course in self.academic_repo.get_plan_courses(plan.sp_id):
                course = self.academic_repo.get_course(plan_course.course_id)
                if course is not None:
                    courses.append(course)

            pending_plans.append({
                "plan": plan,
                "student": student,
                "program": (
                    self.academic_repo.get_program(student.program_id)
                    if student.program_id is not None
                    else None
                ),
                "courses": courses,
                "plan_credits": sum(course.credits for course in courses),
                "progress": degree_progress,
                "feedback": self.academic_repo.get_feedback_for_advisor_plan(
                    advisor.advisor_id,
                    plan.sp_id,
                ),
            })

        return {"advisor": advisor, "pending_plans": pending_plans}

    def submit_plan_decision(
        self,
        user_id: int,
        sp_id: int,
        decision: str,
        comment: str,
    ) -> bool:
        if decision not in {"Approve", "Request changes"}:
            return False

        advisor = self.academic_repo.get_advisor_by_user_id(user_id)
        if advisor is None:
            return False
        plan = self.academic_repo.get_submitted_plan_for_advisor(
            advisor.advisor_id,
            sp_id,
        )
        if plan is None:
            return False

        feedback = self.academic_repo.get_feedback_for_advisor_plan(
            advisor.advisor_id,
            sp_id,
        )
        if feedback is None:
            feedback = Feedback(
                sp_id=sp_id,
                advisor_id=advisor.advisor_id,
                decision=decision,
                comment=comment.strip(),
            )
        else:
            feedback.decision = decision
            feedback.comment = comment.strip()
        self.academic_repo.save_feedback(feedback)

        plan.status = "Approved" if decision == "Approve" else "Request Changes"
        self.academic_repo.save_semester_plan(plan)
        return True