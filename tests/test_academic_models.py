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
