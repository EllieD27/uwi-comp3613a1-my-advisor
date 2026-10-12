#!/usr/bin/env python3
"""FastStarter project CLI — stdlib argparse (no extra CLI library).

From the project root (venv active, deps installed; ``.env`` optional — falls back to ``.env.example``):

    python manage.py init
    python manage.py run
    python manage.py users
    python manage.py report --name "Student Name" --id "816000000"
    python manage.py usecase
    python manage.py skills-verify
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


def _ensure_models_loaded() -> None:
    import app.models  # noqa: F401


def cmd_init(args: argparse.Namespace) -> None:
    """Create database tables (drops existing by default) and seed demo users."""
    from app.config import get_settings
    from app.database import drop_all, ensure_db_and_tables

    _ensure_models_loaded()
    if args.drop:
        print("Dropping all tables…")
        # Drop can fail on a brand-new empty DB; create path still retries.
        try:
            drop_all()
        except Exception as exc:  # noqa: BLE001
            from app.database import is_db_not_ready_error

            if not is_db_not_ready_error(exc):
                raise
            print(f"Database not ready yet while dropping ({exc}); continuing…")
    print("Creating tables…")
    ensure_db_and_tables()
    print(f"Database ready ({get_settings().database_uri}).")
    if getattr(args, "seed", True):
        cmd_seed(args)


REMOVED_DEMO_STUDENT_USERNAMES = ("lee", "bridget", "rupert")
CORE_REQUIREMENT_CODES = (
    "ACCT 1002", "ACCT 1003", "COMP 1600", "COMP 1601", "COMP 1602",
    "COMP 1603", "COMP 2601", "COMP 2602", "COMP 2603", "COMP 2604",
    "COMP 2605", "COMP 2606", "COMP 2611", "ECON 1001", "ECON 1002",
    "FOUN 1101", "FOUN 1105", "FOUN 1301", "INFO 3609", "MKTG 2001",
    "MGMT 2021", "MGMT 2008", "MGMT 2032",
)


def _purge_demo_student_accounts(session, repo) -> int:
    from sqlmodel import delete, select

    from app.models.academic import Feedback, SemesterPlan, SemesterPlanCourse, Student, StudentCourse

    removed_accounts = 0
    for username in REMOVED_DEMO_STUDENT_USERNAMES:
        account = repo.get_by_username(username)
        matching_students = session.exec(
            select(Student).where(Student.email == f"{username}@example.com")
        ).all()
        if account is not None:
            matching_students.extend(
                session.exec(select(Student).where(Student.user_id == account.id)).all()
            )

        seen_student_ids: set[int] = set()
        for removed_student in matching_students:
            if removed_student.student_id in seen_student_ids:
                continue
            seen_student_ids.add(removed_student.student_id)
            removed_plans = session.exec(
                select(SemesterPlan).where(
                    SemesterPlan.student_id == removed_student.student_id
                )
            ).all()
            for removed_plan in removed_plans:
                session.exec(
                    delete(SemesterPlanCourse).where(
                        SemesterPlanCourse.sp_id == removed_plan.sp_id
                    )
                )
                session.exec(delete(Feedback).where(Feedback.sp_id == removed_plan.sp_id))
                session.delete(removed_plan)
            session.exec(
                delete(StudentCourse).where(
                    StudentCourse.student_id == removed_student.student_id
                )
            )
            session.delete(removed_student)

        if matching_students:
            session.commit()
        if account is not None:
            session.delete(account)
            session.commit()
            removed_accounts += 1
    return removed_accounts


def _sync_program_requirements(session, program) -> int:
    from sqlmodel import delete, select

    from app.models.academic import Course, ProgramRequirement

    session.exec(
        delete(ProgramRequirement).where(
            ProgramRequirement.program_id == program.program_id
        )
    )
    courses = session.exec(select(Course).order_by(Course.code)).all()
    core_codes = set(CORE_REQUIREMENT_CODES)
    for course in courses:
        category = (
            "Foundation" if course.code == "FOUN 1101"
            else "Core" if course.code in core_codes
            else "Electives"
        )
        session.add(
            ProgramRequirement(
                program_id=program.program_id,
                course_id=course.course_id,
                category=category,
                required=True,
                note="Wireframe course-count progress category",
            )
        )
    session.commit()
    return len(courses)


def cmd_sync_degree_requirements(args: argparse.Namespace) -> None:
    """Update only degree requirement categories, preserving student work."""
    from sqlmodel import select

    from app.database import ensure_db_and_tables, get_cli_session
    from app.models.academic import Program

    _ensure_models_loaded()
    ensure_db_and_tables()
    with get_cli_session() as session:
        program = session.exec(
            select(Program).where(Program.name == "BSc Computer Science")
        ).one_or_none()
        if program is None:
            raise SystemExit("BSc Computer Science program not found; run `python manage.py seed` first.")
        count = _sync_program_requirements(session, program)
    print(f"Updated {count} degree requirements (23 Core/Foundation courses, 8 Electives); student plans and transcripts were preserved.")


def cmd_purge_demo_students(args: argparse.Namespace) -> None:
    """Remove retired demo student accounts and every related academic record."""
    from app.database import ensure_db_and_tables, get_cli_session
    from app.repositories.user import UserRepository

    _ensure_models_loaded()
    ensure_db_and_tables()
    with get_cli_session() as session:
        removed = _purge_demo_student_accounts(session, UserRepository(session))
    print(f"Removed {removed} retired demo student account(s) and related records.")


def cmd_seed(args: argparse.Namespace) -> None:
    """Insert demo users and starter academic records for MyAdvisor."""
    from sqlmodel import delete, select

    from app.database import ensure_db_and_tables, get_cli_session
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
    from app.repositories.user import UserRepository
    from app.schemas.user import AdminCreate, RegularUserCreate
    from app.utilities.security import encrypt_password

    _ensure_models_loaded()
    ensure_db_and_tables()

    student_seed_specs = [
        {
            "name": "Ian McCarthy", "username": "ian", "email": "ian@example.com",
            "completed": [],
            "plan": ["ACCT 1002", "COMP 1600", "COMP 1601", "ECON 1001", "FOUN 1101"],
        },
        {
            "name": "Celeste Weston", "username": "celeste", "email": "celeste@example.com",
            "completed": [
                ("COMP 1601", "B+"), ("COMP 1602", "C"), ("COMP 1603", "B"),
                ("ACCT 1002", "A-"), ("ACCT 1003", "A"),
            ],
            "plan": ["COMP 1603", "ACCT 1002", "ECON 1001", "ECON 1002", "FOUN 1101"],
        },
        {
            "name": "Kate Baxter", "username": "kate", "email": "kate@example.com",
            "completed": [
                ("COMP 1601", "C"), ("COMP 1602", "B"), ("COMP 1603", "B+"),
                ("ACCT 1002", "A-"), ("ACCT 1003", "A"), ("ECON 1001", "B+"),
                ("ECON 1002", "B"), ("FOUN 1101", "A-"), ("FOUN 1105", "B+"),
                ("FOUN 1301", "B"),
            ],
            "plan": ["COMP 2601", "COMP 2602", "COMP 2605", "COMP 2606", "COMP 2611"],
        },
        {
            "name": "Nelly miller", "username": "nelly", "email": "nelly@example.com",
            "completed": [
                ("ECON 1001", "B+"), ("ECON 1002", "B"), ("FOUN 1101", "A-"),
                ("FOUN 1105", "B+"), ("FOUN 1301", "B"),
            ],
            "plan": ["COMP 2601", "COMP 2602", "COMP 2605", "COMP 2606", "COMP 2611"],
            "plan_status": "Submitted",
        },
    ]

    demo_users = [
        ("bob", "bob@example.com", "bobpass", "regular_user"),
        ("admin", "admin@example.com", "adminpass", "admin"),
    ] + [
        (spec["username"], spec["email"], f'{spec["username"]}pass', "regular_user")
        for spec in student_seed_specs
    ]

    created = 0
    skipped = 0
    with get_cli_session() as session:
        repo = UserRepository(session)
        removed = _purge_demo_student_accounts(session, repo)
        if removed:
            print(f"  remove {removed} retired demo student account(s) and related records")

        for username, email, password, role in demo_users:
            if repo.get_by_username(username):
                print(f"  skip  {username} (already exists)")
                skipped += 1
                continue
            payload_cls = AdminCreate if role == "admin" else RegularUserCreate
            repo.create(
                payload_cls(
                    username=username,
                    email=email,
                    password=encrypt_password(password),
                    role=role,
                )
            )
            print(f"  create {username} ({role})")
            created += 1

        program = session.exec(select(Program).where(Program.name == "BSc Computer Science")).one_or_none()
        if program is None:
            program = Program(
                name="BSc Computer Science",
                degree_title="Bachelor of Science",
                required_credits=93,
                max_credits=15,
            )
            session.add(program)
            session.commit()
            session.refresh(program)
        else:
            program.required_credits = 93
            program.max_credits = 15
            session.add(program)
            session.commit()

        advisor = session.exec(select(Advisor).where(Advisor.email == "advisor@example.com")).one_or_none()
        if advisor is None:
            advisor = Advisor(
                user_id=repo.get_by_username("admin").id,
                name="Dr. Amelia Grant",
                email="advisor@example.com",
            )
            session.add(advisor)
            session.commit()
            session.refresh(advisor)

        student = session.exec(select(Student).where(Student.email == "bob@example.com")).one_or_none()
        if student is None:
            bob_user = repo.get_by_username("bob")
            student = Student(
                user_id=bob_user.id,
                program_id=program.program_id,
                advisor_id=advisor.advisor_id,
                name="Bob Student",
                email="bob@example.com",
                status="active",
            )
            session.add(student)
            session.commit()
            session.refresh(student)

        course_specs = [
            ("ACCT 1002", "Introduction to Financial Accounting", 3),
            ("ACCT 1003", "Introduction to Cost and Management Accounting", 3),
            ("COMP 1600", "Introduction to Computing Concepts", 3),
            ("COMP 1601", "Computer Programming I", 3),
            ("COMP 1602", "Computer Programming II", 3),
            ("COMP 1603", "Computer Programming III", 3),
            ("COMP 2601", "Computer Architecture", 3),
            ("COMP 2602", "Computer Networks", 3),
            ("COMP 2603", "Object-Oriented Programming", 3),
            ("COMP 2604", "Operating Systems", 3),
            ("COMP 2605", "Enterprise Database Systems", 3),
            ("COMP 2606", "Software Engineering I", 3),
            ("COMP 2611", "Data Structures", 3),
            ("ECON 1001", "Introduction to Microeconomics", 3),
            ("ECON 1002", "Introduction to Macroeconomics", 3),
            ("FOUN 1101", "Caribbean Civilisation", 3),
            ("FOUN 1105", "Scientific and Technical Writing", 3),
            ("FOUN 1301", "Law, Governance, Economy and Society", 3),
            ("INFO 3609", "Internship I", 3),
            ("MGMT 2021", "Business Law I", 3),
            ("MGMT 2008", "Organizational Behaviour", 3),
            ("MGMT 2032", "Managerial Economics", 3),
            ("MKTG 2001", "Principles of Marketing", 3),
            ("MGMT 2012", "Quantitative Methods", 3),
            ("COMP 3603", "Human-Computer Interaction", 3),
            ("COMP 3605", "Advanced Computing II", 3),
            ("COMP 3606", "Wireless and Mobile Computing", 3),
            ("COMP 3613", "Software Engineering II", 3),
            ("INFO 2605", "Information Systems Elective I", 3),
            ("INFO 3606", "Information Systems Elective II", 3),
            ("MATH 2250", "Discrete Mathematics", 3),
        ]
        allowed_course_codes = {code for code, _, _ in course_specs}
        existing_courses = {course.code: course for course in session.exec(select(Course)).all()}

        # Remove stale starter/demo codes and dependent rows; the demo catalog must
        # contain only codes present in the student's wireframes.
        for code, course in existing_courses.items():
            if code in allowed_course_codes:
                continue
            session.exec(delete(ProgramRequirement).where(ProgramRequirement.course_id == course.course_id))
            session.exec(delete(StudentCourse).where(StudentCourse.course_id == course.course_id))
            session.exec(delete(SemesterPlanCourse).where(SemesterPlanCourse.course_id == course.course_id))
            session.exec(delete(CoursePrerequisite).where(
                (CoursePrerequisite.course_id == course.course_id)
                | (CoursePrerequisite.prereq_id == course.course_id)
            ))
            session.delete(course)
        session.commit()
        existing_courses = {course.code: course for course in session.exec(select(Course)).all()}

        for code, title, credits in course_specs:
            course = existing_courses.get(code)
            faculty = code.rstrip("0123456789 ").strip()
            department = "Science" if code.startswith(("COMP", "INFO", "MATH")) else faculty.title()
            if course is None:
                course = Course(
                    code=code,
                    title=title,
                    credits=credits,
                    faculty=faculty,
                    department=department,
                )
            else:
                course.title = title
                course.credits = credits
                course.faculty = faculty
                course.department = department
            session.add(course)
        session.commit()
        courses_by_code = {course.code: course for course in session.exec(select(Course)).all()}

        grade_scale_values = [
            ("A+", 4.3), ("A", 4.0), ("A-", 3.7), ("B+", 3.30), ("B", 3.00),
            ("B-", 2.7), ("C+", 2.30), ("C", 2.00), ("F", 1.70),
        ]
        for grade, points in grade_scale_values:
            session.merge(GradeScale(grade=grade, points=points))
        session.commit()

        for spec in student_seed_specs:
            account = repo.get_by_username(spec["username"])
            seeded_student = session.exec(
                select(Student).where(Student.email == spec["email"])
            ).one_or_none()
            if seeded_student is None:
                seeded_student = Student(
                    user_id=account.id,
                    program_id=program.program_id,
                    advisor_id=advisor.advisor_id,
                    name=spec["name"],
                    email=spec["email"],
                    status="active",
                )
                session.add(seeded_student)
                session.commit()
                session.refresh(seeded_student)
            else:
                seeded_student.user_id = account.id
                seeded_student.program_id = program.program_id
                seeded_student.advisor_id = advisor.advisor_id
                seeded_student.name = spec["name"]
                seeded_student.status = "active"
                session.add(seeded_student)
                session.commit()

            session.exec(
                delete(StudentCourse).where(StudentCourse.student_id == seeded_student.student_id)
            )
            old_plans = session.exec(
                select(SemesterPlan).where(SemesterPlan.student_id == seeded_student.student_id)
            ).all()
            for old_plan in old_plans:
                session.exec(delete(SemesterPlanCourse).where(SemesterPlanCourse.sp_id == old_plan.sp_id))
                session.exec(delete(Feedback).where(Feedback.sp_id == old_plan.sp_id))
                session.delete(old_plan)
            session.commit()

            for course_code, grade in spec["completed"]:
                session.add(
                    StudentCourse(
                        student_id=seeded_student.student_id,
                        course_id=courses_by_code[course_code].course_id,
                        grade=grade,
                        sem_completed="2025/2026 Semester 2",
                        status="Completed",
                    )
                )

            seeded_plan = SemesterPlan(
                student_id=seeded_student.student_id,
                semester="2026/2027 Semester 1",
                status=spec.get("plan_status", "Draft"),
                submitted_at=(
                    datetime.now(timezone.utc)
                    if spec.get("plan_status") == "Submitted"
                    else None
                ),
                notes="Demo semester plan",
            )
            session.add(seeded_plan)
            session.commit()
            session.refresh(seeded_plan)
            for course_code in spec["plan"]:
                session.add(
                    SemesterPlanCourse(
                        sp_id=seeded_plan.sp_id,
                        course_id=courses_by_code[course_code].course_id,
                    )
                )
            session.commit()

        # Rebuild the demo requirement and transcript rows to match the wireframe.
        _sync_program_requirements(session, program)
        session.exec(delete(StudentCourse).where(StudentCourse.student_id == student.student_id))

        completed_codes = list(CORE_REQUIREMENT_CODES)
        sample_grades = {
            "ACCT 1002": "A", "ACCT 1003": "A", "COMP 1600": "A-", "COMP 1601": "A",
            "COMP 1602": "A-", "COMP 1603": "A-", "COMP 2601": "B", "COMP 2602": "B+",
            "COMP 2603": "B+", "COMP 2604": "A", "COMP 2605": "B", "COMP 2606": "A",
            "COMP 2611": "A", "ECON 1001": "A", "ECON 1002": "A", "FOUN 1101": "B+",
            "FOUN 1105": "B", "FOUN 1301": "C+", "INFO 3609": "A+", "MKTG 2001": "B",
            "MGMT 2021": "B", "MGMT 2008": "B+", "MGMT 2032": "A-",
        }
        for code in completed_codes:
            session.add(
                StudentCourse(
                    student_id=student.student_id,
                    course_id=courses_by_code[code].course_id,
                    grade=sample_grades[code],
                    sem_completed="2024/2025",
                    status="Completed",
                )
            )

        semester_plan = session.exec(
            select(SemesterPlan).where(SemesterPlan.student_id == student.student_id)
        ).first()
        if semester_plan is None:
            semester_plan = SemesterPlan(student_id=student.student_id)
        semester_plan.semester = "2026/2027 Semester 1"
        semester_plan.status = "Request Changes"
        semester_plan.notes = "Ready for advisor feedback"
        session.add(semester_plan)
        session.commit()
        session.refresh(semester_plan)

        session.exec(delete(SemesterPlanCourse).where(SemesterPlanCourse.sp_id == semester_plan.sp_id))
        for code in ["COMP 3603", "COMP 3606", "COMP 3613"]:
            session.add(
                SemesterPlanCourse(
                    sp_id=semester_plan.sp_id,
                    course_id=courses_by_code[code].course_id,
                )
            )

        feedback = session.exec(select(Feedback).where(Feedback.sp_id == semester_plan.sp_id)).one_or_none()
        if feedback is None:
            feedback = Feedback(sp_id=semester_plan.sp_id, advisor_id=advisor.advisor_id)
        feedback.comment = "Minimum courses per full-time semester is 4 courses. You can do 4 courses in each semester to achieve the remaining 8 courses."
        feedback.decision = "Request changes"
        session.add(feedback)

        prerequisite_specs = [
            ("COMP 1602", "COMP 1601"),
            ("COMP 3613", "COMP 2606"),
            ("COMP 2611", "COMP 1602"),
            ("COMP 2605", "COMP 1601"),
            ("COMP 3606", "COMP 2602"),
            ("COMP 3605", "MATH 2250"),
        ]
        prerequisite_course_ids = [
            courses_by_code[code].course_id for code, _ in prerequisite_specs
        ]
        session.exec(
            delete(CoursePrerequisite).where(
                CoursePrerequisite.course_id.in_(prerequisite_course_ids)
            )
        )
        for course_code, prerequisite_code in prerequisite_specs:
            session.add(
                CoursePrerequisite(
                    course_id=courses_by_code[course_code].course_id,
                    prereq_id=courses_by_code[prerequisite_code].course_id,
                )
            )

        session.commit()

    print(f"Seed done — created {created}, skipped {skipped}.")
    print("Demo student logins: bob/bobpass, ian/ianpass, celeste/celestepass, kate/katepass, nelly/nellypass")
    print("Admin login: admin/adminpass")


def cmd_run(args: argparse.Namespace) -> None:
    """Start the FastAPI app with Uvicorn."""
    import uvicorn

    from app.config import get_settings

    settings = get_settings()
    bind_host = args.host or settings.app_host
    bind_port = args.port or settings.app_port
    if args.reload is None:
        use_reload = settings.env.lower() != "production"
    else:
        use_reload = args.reload
    print(f"Starting FastStarter on http://{bind_host}:{bind_port} (reload={use_reload})")
    uvicorn.run(
        "app.main:app",
        host=bind_host,
        port=bind_port,
        reload=use_reload,
    )


def cmd_report(args: argparse.Namespace) -> None:
    """Build the submission package: merge judge, package transcripts, write PDF.

    Guide must (1) write ``docs/judge.md`` and (2) pull every Guide chat into
    ``docs/transcripts/*.md`` before this command. Report only packages those files.
    """
    from app.report_pdf import export_report
    from app.skill_integrity import format_report, verify

    result = export_report(
        name=args.name,
        student_id=args.student_id,
        source=None if args.src is None else Path(args.src),
        output=None if args.output is None else Path(args.output),
    )
    print()
    print("Report package:")
    print(
        f"  Judge:       {'merged docs/judge.md' if result.judge_merged else 'MISSING - Guide must run student-judge first'}"
    )
    print(
        f"  Transcripts: {result.transcript_count} chat(s) in docs/transcripts/"
        + (
            ""
            if result.transcript_count
            else " (EMPTY - Guide must pull Copilot/Cursor/OpenCode chats first)"
        )
    )
    if result.transcript_zip:
        print(f"  Zip:         {result.transcript_zip.as_posix()}")
    print(f"  PDF:         {result.pdf_path.as_posix()}")
    print(format_report(verify()))


def cmd_transcripts(args: argparse.Namespace) -> None:
    """Package agent-written markdown under docs/transcripts/ (+ zip)."""
    from app.transcript_export import package_transcripts

    result = package_transcripts(make_zip=not args.no_zip)
    if result.found == 0:
        print(
            "Warning: no chat markdown in docs/transcripts/. "
            "The Guide agent must pull every Guide chat for this project "
            "(Copilot Agent, Cursor, or OpenCode) into docs/transcripts/<slug>.md first."
        )
        raise SystemExit(2)
    print(f"Submission package ready: {result.out_dir}")
    if result.zip_path:
        print(f"Zip for submission: {result.zip_path}")


def cmd_skills_verify(args: argparse.Namespace) -> None:
    """Check course skill files against .agents/skills.lock.json."""
    from app.skill_integrity import format_report, verify

    result = verify()
    print(format_report(result))
    if not result.ok:
        raise SystemExit(1)


def cmd_usecase(args: argparse.Namespace) -> None:
    """Render docs/diagrams/use-case.json to a UML use-case PNG."""
    from app.usecase_diagram import render_usecase_png

    dest = render_usecase_png(
        spec_path=None if args.spec is None else Path(args.spec),
        output=None if args.output is None else Path(args.output),
    )
    print(f"Wrote {dest}")


def cmd_skills_lock(args: argparse.Namespace) -> None:
    """Rewrite the skill lockfile (course authors only)."""
    from app.skill_integrity import write_lock

    dest = write_lock()
    print(f"Wrote {dest}")


def cmd_users(args: argparse.Namespace) -> None:
    """List users currently in the database."""
    from sqlmodel import select

    from app.database import get_cli_session
    from app.models.user import User

    _ensure_models_loaded()
    with get_cli_session() as session:
        users = session.exec(select(User)).all()
        if not users:
            print("No users found. Run: python manage.py init")
            return
        for user in users:
            print(
                f"  id={user.id}  username={user.username}  "
                f"role={user.role}  email={user.email}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python manage.py",
        description="FastStarter Python CLI — init database, seed demo data, run the app.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="Create DB tables and seed demo users (drops existing tables by default)",
    )
    p_init.add_argument(
        "--no-drop",
        dest="drop",
        action="store_false",
        help="Create tables without dropping existing ones",
    )
    p_init.add_argument(
        "--no-seed",
        dest="seed",
        action="store_false",
        help="Skip demo user seed after creating tables",
    )
    p_init.set_defaults(drop=True, seed=True, func=cmd_init)

    p_seed = sub.add_parser(
        "seed",
        help="Insert demo users only (idempotent; also runs as part of init)",
    )
    p_seed.set_defaults(func=cmd_seed)

    p_purge_students = sub.add_parser(
        "purge-demo-students",
        help="Remove retired demo students Lee, Bridget, and Rupert with their related records",
    )
    p_purge_students.set_defaults(func=cmd_purge_demo_students)

    p_sync_progress = sub.add_parser(
        "sync-degree-requirements",
        help="Update degree requirement categories/counts without changing student plans or transcripts",
    )
    p_sync_progress.set_defaults(func=cmd_sync_degree_requirements)

    p_run = sub.add_parser("run", help="Start the web app (uvicorn)")
    p_run.add_argument("--host", default=None, help="Bind host")
    p_run.add_argument("--port", type=int, default=None, help="Bind port")
    reload_group = p_run.add_mutually_exclusive_group()
    reload_group.add_argument(
        "--reload", dest="reload", action="store_true", default=None, help="Enable auto-reload"
    )
    reload_group.add_argument(
        "--no-reload", dest="reload", action="store_false", help="Disable auto-reload"
    )
    p_run.set_defaults(func=cmd_run, reload=None)

    p_users = sub.add_parser("users", help="List users in the database")
    p_users.set_defaults(func=cmd_users)

    p_report = sub.add_parser(
        "report",
        help=(
            "Build submission package: merge docs/judge.md, package docs/transcripts/, "
            "write docs/report.pdf (Guide pulls chats + runs student-judge first)"
        ),
    )
    p_report.add_argument("--name", required=True, help="Student name (printed on the PDF cover)")
    p_report.add_argument("--id", dest="student_id", required=True, help="Student ID (PDF only)")
    p_report.add_argument("--src", default=None, help="Markdown path (default: docs/report.md)")
    p_report.add_argument("--output", default=None, help="PDF path (default: docs/report.pdf)")
    p_report.set_defaults(func=cmd_report)

    p_transcripts = sub.add_parser(
        "transcripts",
        help="Package agent-written docs/transcripts/*.md into INDEX + zip (no IDE scrape)",
    )
    p_transcripts.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip writing docs/transcripts.zip",
    )
    p_transcripts.set_defaults(func=cmd_transcripts)

    p_usecase = sub.add_parser(
        "usecase",
        help="Render docs/diagrams/use-case.json to a UML use-case PNG",
    )
    p_usecase.add_argument("--spec", default=None, help="JSON spec (default: docs/diagrams/use-case.json)")
    p_usecase.add_argument("--output", default=None, help="PNG path (default: docs/diagrams/use-case.png)")
    p_usecase.set_defaults(func=cmd_usecase)

    p_skills_verify = sub.add_parser(
        "skills-verify",
        help="Check course skills against .agents/skills.lock.json",
    )
    p_skills_verify.set_defaults(func=cmd_skills_verify)

    p_skills_lock = sub.add_parser(
        "skills-lock",
        help="Rewrite .agents/skills.lock.json (course authors; needs FASTSTARTER_SKILLS_LOCK=1)",
    )
    p_skills_lock.set_defaults(func=cmd_skills_lock)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
