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