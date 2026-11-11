# Consolidated Assignment 2 unit tests

# --- test_academic_models.py ---
from sqlalchemy import CheckConstraint, UniqueConstraint

from app.models import (
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


def test_academic_er_draft_models_exist_with_expected_keys():
    grade_scale_fields = set(GradeScale.model_fields)
    assert {"grade", "points"}.issubset(grade_scale_fields)

    student_fields = set(Student.model_fields)
    assert {"student_id", "program_id", "advisor_id", "name", "email", "status"}.issubset(student_fields)

    advisor_fields = set(Advisor.model_fields)
    assert {"advisor_id", "name", "email"}.issubset(advisor_fields)

    program_fields = set(Program.model_fields)
    assert {"program_id", "name", "degree_title", "required_credits", "max_credits"}.issubset(program_fields)

    course_fields = set(Course.model_fields)
    assert {"course_id", "code", "title", "credits", "faculty", "department"}.issubset(course_fields)

    requirement_fields = set(ProgramRequirement.model_fields)
    assert {"pr_id", "program_id", "course_id", "category", "required", "note"}.issubset(requirement_fields)

    plan_fields = set(SemesterPlan.model_fields)
    assert {"sp_id", "student_id", "semester", "created_at", "submitted_at", "status", "notes"}.issubset(plan_fields)

    plan_course_fields = set(SemesterPlanCourse.model_fields)
    assert {"spc_id", "sp_id", "course_id"}.issubset(plan_course_fields)

    feedback_fields = set(Feedback.model_fields)
    assert {"feedback_id", "sp_id", "advisor_id", "created_at", "comment", "decision"}.issubset(feedback_fields)

    student_course_fields = set(StudentCourse.model_fields)
    assert {"sc_id", "student_id", "course_id", "grade", "sem_completed", "status"}.issubset(student_course_fields)

    prerequisite_fields = set(CoursePrerequisite.model_fields)
    assert {"cp_id", "course_id", "prereq_id"}.issubset(prerequisite_fields)


def test_semester_plan_course_prevents_duplicate_course_entries():
    unique_course_pairs = [
        constraint
        for constraint in SemesterPlanCourse.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns} == {"sp_id", "course_id"}
    ]

    assert len(unique_course_pairs) == 1


def test_feedback_decision_is_restricted_to_erd_values():
    decision_constraints = [
        constraint
        for constraint in Feedback.__table__.constraints
        if isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_feedback_decision_allowed"
    ]

    assert len(decision_constraints) == 1
    assert "Approve" in str(decision_constraints[0].sqltext)
    assert "Request changes" in str(decision_constraints[0].sqltext)

# --- test_academic_repository.py ---
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

# --- test_advisor_review.py ---
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

def test_request_changes_requires_a_comment():
    repo = AdvisorRepositoryStub()
    service = AdvisorReviewService(repo)

    assert service.submit_plan_decision(2, 22, "Request changes", "") is False
    assert repo.saved_feedback == []
    assert repo.plan.status == "Submitted"

# --- test_advisor_template.py ---
from pathlib import Path


def test_advisor_review_template_contains_wireframe_details_and_gpa():
    template = Path("app/templates/admin.html").read_text(encoding="utf-8")

    assert "Pending Plans" in template
    assert "GPA · Credit-weighted" in template
    assert 'value="Request changes"' in template
    assert 'value="Approve"' in template
    assert "Plan Courses" in template


def test_build_plan_course_options_are_scrollable():
    template = Path("app/templates/build_plan.html").read_text(encoding="utf-8")

    assert "max-height: 440px" in template
    assert "overflow-y: auto" in template
    assert "grouped.keys()|sort" in template

# --- test_degree_progress.py ---
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

class GpaRepository(DegreeProgressRepository):
    def __init__(self):
        super().__init__()
        ids = self.course_ids
        self.student_courses = [
            SimpleNamespace(course_id=ids["COMP 1600"], grade="A", status="Completed", sem_completed="2024/2025"),
            SimpleNamespace(course_id=ids["COMP 1601"], grade="B", status="Completed", sem_completed="2024/2025"),
            SimpleNamespace(course_id=ids["COMP 1602"], grade=None, status="In progress", sem_completed=""),
        ]

    def get_grade_scale(self, grade):
        points = {"A": 4.0, "B": 3.0}.get(grade)
        return SimpleNamespace(grade=grade, points=points) if points is not None else None


def test_gpa_is_credit_weighted_and_ignores_ungraded_courses():
    result = DegreeProgressService(GpaRepository()).get_student_progress(10)

    assert result["gpa"] == 3.5

# --- test_my_plans_service.py ---
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

# --- test_semester_plan_service.py ---
from types import SimpleNamespace

from app.services.semester_plan import SemesterPlanService


class DummyAcademicRepository:
    def __init__(self):
        self.courses = {
            "COMP 3603": SimpleNamespace(course_id=1, code="COMP 3603", title="Human-Computer Interaction", credits=3),
            "COMP 3605": SimpleNamespace(course_id=2, code="COMP 3605", title="Advanced Computing II", credits=3),
            "COMP 3606": SimpleNamespace(course_id=3, code="COMP 3606", title="Wireless and Mobile Computing", credits=3),
            "COMP 3613": SimpleNamespace(course_id=4, code="COMP 3613", title="Software Engineering II", credits=3),
            "INFO 2605": SimpleNamespace(course_id=5, code="INFO 2605", title="Information Systems Elective I", credits=3),
            "INFO 3606": SimpleNamespace(course_id=6, code="INFO 3606", title="Information Systems Elective II", credits=3),
            "MATH 2250": SimpleNamespace(course_id=7, code="MATH 2250", title="Discrete Mathematics", credits=3),
            "MGMT 2012": SimpleNamespace(course_id=8, code="MGMT 2012", title="Quantitative Methods", credits=3),
        }
        self.prereq_map = {
            2: [SimpleNamespace(prereq_id=7)],
        }
        self.plan_course_ids = {1, 3, 4}
        self.completed_course_ids = {1, 3, 4}

    def get_student_by_user_id(self, user_id):
        return SimpleNamespace(student_id=1, user_id=user_id, program_id=1)

    def get_program(self, program_id):
        return SimpleNamespace(program_id=program_id, max_credits=15)

    def get_student_plans(self, student_id):
        return [SimpleNamespace(sp_id=10, student_id=student_id, status="Draft", semester="2026/2027 Semester 1")]

    def get_plan_courses(self, sp_id):
        return [
            SimpleNamespace(course_id=1),
            SimpleNamespace(course_id=3),
            SimpleNamespace(course_id=4),
        ]

    def get_student_courses(self, student_id):
        return [
            SimpleNamespace(course_id=1, status="Completed"),
            SimpleNamespace(course_id=3, status="Completed"),
            SimpleNamespace(course_id=4, status="Completed"),
        ]

    def get_passed_course_ids(self, student_id):
        return set(self.completed_course_ids)

    def get_course(self, course_id):
        for course in self.courses.values():
            if course.course_id == course_id:
                return course
        return None

    def get_course_by_code(self, code):
        return self.courses.get(code)

    def get_course_prerequisites(self, course_id):
        return self.prereq_map.get(course_id, [])

    def get_plan_course(self, sp_id, course_id):
        if course_id in {1, 3, 4}:
            return SimpleNamespace(sp_id=sp_id, course_id=course_id)
        return None

    def get_courses_by_codes(self, codes):
        return [self.courses[code] for code in codes if code in self.courses]


def test_build_plan_service_marks_prerequisite_gap_and_selected_courses():
    repo = DummyAcademicRepository()
    service = SemesterPlanService(repo)

    view = service.get_build_plan_view(1)

    assert view["selected_codes"] == ["COMP 3603", "COMP 3606", "COMP 3613"]
    assert view["plan_total_credits"] == 9
    assert view["max_credits"] == 15
    assert all(course.credits == 3 for course in repo.courses.values())
    assert any(item["code"] == "COMP 3603" and item["status"] == "Added" for item in view["available_courses"])
    assert view["checks_passed"] is True
    assert [item["code"] for item in view["available_courses"]] == sorted(
        item["code"] for item in view["available_courses"]
    )


def test_build_plan_catalog_is_bob_completed_and_planned_courses_in_code_order():
    assert len(SemesterPlanService.AVAILABLE_CODES) == 27
    assert SemesterPlanService.AVAILABLE_CODES == tuple(sorted(SemesterPlanService.AVAILABLE_CODES))


def test_completed_course_is_marked_and_cannot_be_added_again():
    class TrackingDB:
        def __init__(self):
            self.added = []

        def add(self, obj):
            self.added.append(obj)

        def commit(self):
            pass

    repo = DummyAcademicRepository()
    repo.db = TrackingDB()
    repo.get_plan_courses = lambda sp_id: []
    repo.get_plan_course = lambda sp_id, course_id: None
    service = SemesterPlanService(repo)

    view = service.get_build_plan_view(1)

    assert next(item for item in view["available_courses"] if item["code"] == "COMP 3603")["status"] == "Completed"
    assert service.add_course_to_plan(1, "COMP 3603") is False
    assert repo.db.added == []


def test_semester_plan_service_add_and_submit_update_plan_state():
    plan = SimpleNamespace(
        sp_id=10,
        student_id=1,
        semester="2026/2027 Semester 1",
        status="Draft",
        submitted_at=None,
    )

    class TrackingDB:
        def __init__(self):
            self.added = []

        def add(self, obj):
            self.added.append(obj)

        def commit(self):
            pass

    repo = DummyAcademicRepository()
    repo.db = TrackingDB()
    repo.courses["ACCT 1002"] = SimpleNamespace(
        course_id=9,
        code="ACCT 1002",
        title="Introduction to Financial Accounting",
        credits=3,
    )
    repo.plan = plan
    repo.plan_courses = {1, 3, 4}
    repo.get_student_plans = lambda student_id: [repo.plan]

    def get_plan_course(sp_id, course_id):
        if course_id in repo.plan_courses:
            return SimpleNamespace(sp_id=sp_id, course_id=course_id)
        return None

    repo.get_plan_course = get_plan_course
    service = SemesterPlanService(repo)

    assert service.add_course_to_plan(1, "ACCT 1002") is True
    assert any(obj.course_id == 9 for obj in repo.db.added if hasattr(obj, "course_id"))

    assert service.submit_plan(1) is True
    assert repo.plan.status == "Submitted"
    assert repo.plan.submitted_at is not None


def test_add_course_rejects_plan_that_would_exceed_credit_limit():
    class TrackingDB:
        def __init__(self):
            self.added = []

        def add(self, obj):
            self.added.append(obj)

        def commit(self):
            pass

    repo = DummyAcademicRepository()
    repo.db = TrackingDB()
    repo.courses["ACCT 1002"] = SimpleNamespace(
        course_id=9,
        code="ACCT 1002",
        title="Introduction to Financial Accounting",
        credits=3,
    )
    repo.get_plan_courses = lambda sp_id: [
        SimpleNamespace(course_id=course_id)
        for course_id in (1, 3, 4, 5, 6)
    ]
    repo.get_plan_course = lambda sp_id, course_id: None

    service = SemesterPlanService(repo)
    view = service.get_build_plan_view(1)

    assert view["plan_total_credits"] == 15
    assert next(item for item in view["available_courses"] if item["code"] == "ACCT 1002")["status"] == "Max credits reached"
    assert service.add_course_to_plan(1, "ACCT 1002") is False
    assert repo.db.added == []


def test_add_course_rejects_course_when_prerequisite_is_not_passed():
    class TrackingDB:
        def __init__(self):
            self.added = []

        def add(self, obj):
            self.added.append(obj)

        def commit(self):
            pass

    repo = DummyAcademicRepository()
    repo.db = TrackingDB()
    repo.courses["COMP 1602"] = SimpleNamespace(
        course_id=9,
        code="COMP 1602",
        title="Computer Programming II",
        credits=3,
    )
    repo.prereq_map[9] = [SimpleNamespace(prereq_id=10)]
    repo.get_plan_courses = lambda sp_id: []
    repo.get_plan_course = lambda sp_id, course_id: None
    repo.completed_course_ids = {1, 3, 4}  # COMP 1601 is not in the passed-course set.

    service = SemesterPlanService(repo)

    assert service.add_course_to_plan(1, "COMP 1602") is False
    assert repo.db.added == []

# --- test_smoke.py ---
