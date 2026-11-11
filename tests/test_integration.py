from urllib.parse import urlparse
from sqlmodel import select
from app.models.academic import Feedback, SemesterPlan
from app.models.academic import SemesterPlanCourse, Student


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200


def login(client, username, password, next_path=""):
    return client.post(
        "/login",
        data={"username": username, "password": password, "next": next_path},
        follow_redirects=False,
    )


def test_public_landing_page_is_available(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "MyAdvisor" in response.text


def test_student_dashboard_requires_login(client):
    response = client.get("/app", follow_redirects=False)

    assert response.status_code == 303
    assert urlparse(response.headers["location"]).path == "/login"


def test_authenticated_student_can_view_dashboard(client):
    login_response = login(client, "student", "studentpass")

    assert login_response.status_code == 303

    response = client.get("/app")

    assert response.status_code == 200
    assert "Degree Progress" in response.text


def test_regular_user_cannot_view_admin_dashboard(client):
    login_response = login(client, "student", "studentpass")

    assert login_response.status_code == 303

    response = client.get("/admin")

    assert response.status_code == 401


def test_admin_can_view_admin_dashboard(client):
    login_response = login(client, "admin", "adminpass")

    assert login_response.status_code == 303
    assert urlparse(login_response.headers["location"]).path == "/admin"

    response = client.get("/admin")

    assert response.status_code == 200
    assert "Pending Plans" in response.text


def test_users_api_returns_user_response_shape(client):
    response = client.get("/api/users", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers["location"]

    login(client, "admin", "adminpass")
    response = client.get("/api/users")

    assert response.status_code == 200
    assert {user["username"] for user in response.json()} == {"student", "admin"}
    assert all(set(user) == {"id", "username", "email"} for user in response.json())


def test_student_can_add_and_submit_a_semester_plan(client, session):
    login(client, "student", "studentpass")
    client.post("/app/build-plan", data={"action": "add", "course_code": "COMP 3603"})
    client.post("/app/build-plan", data={"action": "submit"})

    plan = session.exec(select(SemesterPlan)).first()
    assert plan is not None
    assert plan.status == "Submitted"


def test_admin_can_decide_on_submitted_semester_plan(client, session):
    login(client, "student", "studentpass")
    client.post("/app/build-plan", data={"action": "add", "course_code": "COMP 3603"})
    client.post("/app/build-plan", data={"action": "submit"})
    plan = session.exec(select(SemesterPlan)).first()
    assert plan.status == "Submitted"
    client.cookies.clear()

    login(client, "admin", "adminpass")
    queue = client.get("/admin")
    assert "There are no submitted plans awaiting review." not in queue.text

    response = client.post(
        f"/admin/plans/{plan.sp_id}/decision",
        data={"decision": "Approve", "comment": "Plan is ready."},
        follow_redirects=False,
    )
    assert response.status_code == 303

    session.expire_all()
    assert session.get(SemesterPlan, plan.sp_id).status == "Approved"
    feedback = session.exec(select(Feedback)).first()
    assert feedback.decision == "Approve"
    assert "There are no submitted plans awaiting review." in client.get("/admin").text


def _student_submits_plan(client, session):
    login(client, "student", "studentpass")
    client.post("/app/build-plan", data={"action": "add", "course_code": "COMP 3603"})
    client.post("/app/build-plan", data={"action": "submit"})
    return session.exec(select(SemesterPlan)).first()


def test_student_cannot_post_an_advisor_decision(client, session):
    plan = _student_submits_plan(client, session)

    response = client.post(
        f"/admin/plans/{plan.sp_id}/decision",
        data={"decision": "Approve", "comment": "Self approval"},
        follow_redirects=False,
    )

    assert response.status_code in (401, 403)
    session.expire_all()
    assert session.get(SemesterPlan, plan.sp_id).status == "Submitted"
    assert session.exec(select(Feedback)).first() is None


def test_request_changes_without_a_comment_is_rejected(client, session):
    plan = _student_submits_plan(client, session)
    client.cookies.clear()
    login(client, "admin", "adminpass")

    client.post(
        f"/admin/plans/{plan.sp_id}/decision",
        data={"decision": "Request changes", "comment": ""},
        follow_redirects=False,
    )

    session.expire_all()
    assert session.get(SemesterPlan, plan.sp_id).status == "Submitted"
    assert session.exec(select(Feedback)).first() is None


def test_course_with_unmet_prerequisite_cannot_be_added(client, session):
    login(client, "student", "studentpass")

    client.post("/app/build-plan", data={"action": "add", "course_code": "COMP 3605"})

    assert session.exec(select(SemesterPlanCourse)).first() is None


def test_advisor_cannot_decide_on_another_advisors_student(client, session):
    other = session.exec(select(Student).where(Student.name == "Other Student")).first()
    plan = SemesterPlan(
        student_id=other.student_id, semester="2026/2027 Semester 1", status="Submitted"
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)

    login(client, "admin", "adminpass")
    client.post(
        f"/admin/plans/{plan.sp_id}/decision",
        data={"decision": "Approve", "comment": "Not my student."},
        follow_redirects=False,
    )

    session.expire_all()
    assert session.get(SemesterPlan, plan.sp_id).status == "Submitted"
    assert session.exec(select(Feedback)).first() is None