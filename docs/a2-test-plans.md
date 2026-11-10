# Assignment 2 Test Plans

## Unit Test Plan

The original unit tests are retained. The plan below records each unit test
without duplicating or replacing the existing test implementation.

| Unit Test | Input | Expected Output |
|---|---|---|
| `test_academic_er_draft_models_exist_with_expected_keys` | Academic model classes | All required ERD fields exist on the model classes |
| `test_semester_plan_course_prevents_duplicate_course_entries` | A `SemesterPlanCourse` table definition | A unique constraint exists for `sp_id` and `course_id` |
| `test_feedback_decision_is_restricted_to_erd_values` | The `Feedback` table definition | The decision constraint allows `Approve` and `Request changes` |
| `test_passed_course_ids_requires_completed_c_or_better` | Student course records with C, B, F, and in-progress grades | Only completed courses with C-or-better grades are returned |
| `test_dashboard_credit_and_course_count_cards_reconcile_to_93_credits` | A student with completed core courses | Earned credits and core/elective counts match the degree requirements |
| `test_gpa_is_credit_weighted_and_ignores_ungraded_courses` | Completed A and B courses plus an ungraded in-progress course | GPA is calculated as a credit-weighted 3.5 and ignores the ungraded course |
| `test_build_plan_service_marks_prerequisite_gap_and_selected_courses` | Student plan, catalog courses, and prerequisite data | Selected courses, credits, course statuses, and prerequisite checks are correct |
| `test_build_plan_catalog_is_bob_completed_and_planned_courses_in_code_order` | The semester-plan catalog | The catalog contains the expected courses in code order |
| `test_completed_course_is_marked_and_cannot_be_added_again` | A completed course submitted for addition | The course is marked completed and is not added to the plan |
| `test_semester_plan_service_add_and_submit_update_plan_state` | A valid course addition followed by plan submission | The course is added and the plan status changes to `Submitted` |
| `test_add_course_rejects_plan_that_would_exceed_credit_limit` | A plan at the maximum credit limit | The additional course is rejected and no database object is added |
| `test_add_course_rejects_course_when_prerequisite_is_not_passed` | A course whose prerequisite is not passed | The course is rejected and no database object is added |
| `test_my_plans_view_includes_erd_related_courses_and_feedback` | A submitted plan with courses and advisor feedback | The view contains the plan, courses, credits, and feedback |
| `test_my_plans_view_is_empty_for_user_without_student_record` | A user with no student record | The service returns an empty plans view |
| `test_admin_dashboard_includes_assigned_pending_plan_and_gpa` | An advisor with an assigned submitted plan | The dashboard includes the plan, student, courses, credits, progress, and GPA |
| `test_submit_plan_decision_saves_feedback_and_updates_plan_status` | A valid advisor decision and comment | Feedback is saved and the plan status is updated |
| `test_submit_plan_decision_rejects_unassigned_or_invalid_decisions` | An invalid decision or an unassigned advisor | No feedback or plan update is saved |
| `test_request_changes_requires_a_comment` | `Request changes` with an empty comment | The decision is rejected and the plan remains submitted |
| `test_advisor_review_template_contains_wireframe_details_and_gpa` | Advisor review template source | Required review controls, plan details, and GPA labels are present |
| `test_build_plan_course_options_are_scrollable` | Build-plan template source | Course options have the required scrollable layout |

## Integration Test Plan

| Test Dependencies | Description |
|---|---|
| `test_health` | Calls `GET /health` and verifies the application health endpoint returns HTTP 200 |
| `test_public_landing_page_is_available` | With the isolated test database and no login, verifies that the public landing page returns HTTP 200 and displays MyAdvisor |
| `test_student_dashboard_requires_login` | With no authentication cookie, verifies that the student dashboard redirects to the login page |
| `test_authenticated_student_can_view_dashboard` | Logs in as the seeded student and verifies that the student dashboard returns HTTP 200 with degree-progress content |
| `test_regular_user_cannot_view_admin_dashboard` | Logs in as a regular student and verifies that access to the admin dashboard returns HTTP 401 |
| `test_admin_can_view_admin_dashboard` | Logs in as the seeded admin and verifies that the admin dashboard returns HTTP 200 |
| `test_users_api_returns_user_response_shape` | Calls `GET /api/users` and verifies the HTTP 200 response, usernames, and `id`/`username`/`email` response fields |
| `test_student_can_add_and_submit_a_semester_plan` | Logs in as a student, adds `COMP 3603`, submits the plan, and verifies the database status is `Submitted` |
| `test_admin_can_decide_on_submitted_semester_plan` | Creates a submitted student plan, logs in as admin, approves it, and verifies the plan status and feedback record |
| `test_student_cannot_post_an_advisor_decision` | A student attempts to approve a submitted plan and the test verifies authorization failure, unchanged plan status, and no feedback |
| `test_request_changes_without_a_comment_is_rejected` | An admin submits `Request changes` with an empty comment and the test verifies the plan remains `Submitted` with no feedback |
| `test_course_with_unmet_prerequisite_cannot_be_added` | A student attempts to add `COMP 3605` without its prerequisite and the test verifies no plan-course row is created |
| `test_advisor_cannot_decide_on_another_advisors_student` | An admin attempts to decide on a plan assigned to another advisor and the test verifies the plan remains `Submitted` with no feedback |

All integration tests use the isolated in-memory SQLite fixture in
`tests/conftest.py`; they do not modify the development database.

## User Acceptance Test Report

**Tester Name:** Eliana Dookhoo  
**Tester Position:** Software Engineering 2 Student  
**Date of Test (DD/MM/YYYY):** 10 / 11 / 2026

| Test Case | Pre-conditions | Test Steps | Test Criteria | Success (indicate with a check) |
|---|---|---|---|---|
| View Degree Progress | The student account exists and the tester is logged in as a student. | 1. Open the student dashboard.<br>2. Review the degree-progress cards. | The dashboard shows earned credits, required credits, core/elective course counts, and GPA. | ☑ Pass &nbsp;&nbsp; ☐ Fail |
| Build and Submit Semester Plan | The tester is logged in as a student and the course catalogue is available. | 1. Open **Build Plan**.<br>2. Select a valid course.<br>3. Add the course to the plan.<br>4. Submit the plan. | The selected course and total credits are displayed, the submission completes, and the plan status becomes `Submitted`. | ☑ Pass &nbsp;&nbsp; ☐ Fail |
| Review and Approve Semester Plan | A student plan is submitted and the tester is logged in as the assigned advisor/admin. | 1. Open the advisor dashboard.<br>2. Review the submitted plan.<br>3. Enter feedback.<br>4. Select **Approve**. | The plan is removed from the pending queue, the plan status becomes `Approved`, and the feedback is saved. | ☑ Pass &nbsp;&nbsp; ☐ Fail |
| Request Changes to a Semester Plan | A student plan is submitted and the tester is logged in as the assigned advisor/admin. | 1. Open the submitted plan.<br>2. Enter a non-empty feedback comment.<br>3. Select **Request Changes**. | The plan status becomes `Request Changes` and the feedback is available for the student to review. | ☑ Pass &nbsp;&nbsp; ☐ Fail |
| Prevent Invalid Plan Actions | The tester is logged in as a student and selects a course whose prerequisite has not been passed. | 1. Open **Build Plan**.<br>2. Attempt to add the course with the unmet prerequisite. | The course is not added, the plan remains unchanged, and the course status explains that a prerequisite is required. | ☑ Pass &nbsp;&nbsp; ☐ Fail |

### General Comments

______________________________________________________________________________

______________________________________________________________________________

______________________________________________________________________________

**Acceptance Decision:** ☑ Accepted &nbsp;&nbsp; ☐ Rejected  

**Signature:**  

![Eliana Dookhoo signature](assets/eliana-dookhoo-signature.png)
