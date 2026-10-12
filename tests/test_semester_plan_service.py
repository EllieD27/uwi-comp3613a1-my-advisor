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
    assert len(SemesterPlanService.AVAILABLE_CODES) == 26
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
