<!-- student-build:skill-integrity
status: pass
root: e84cd692d0b85eefe546385661958c27d07e8be6c5176a82012f68ccff5c8beb
expected_root: e84cd692d0b85eefe546385661958c27d07e8be6c5176a82012f68ccff5c8beb
mismatches: none
-->

# COMP 3613 Assignment 1

Draft this file with the Guide. **Update it after every phase milestone** before you pause. The use-case diagram is a UML PNG at `docs/diagrams/use-case.png`, linked from this file as `diagrams/use-case.png` (path relative to `docs/report.md`). The model diagram is Mermaid. **Embed wireframe images** as `wireframes/<file>` (files live in `docs/wireframes/`).

Do not put your student ID in this file if you will commit it. The PDF cover adds your name and ID at export time.

## Assigned project

MyAdvisor

## Three workflows

### 1. View Degree Progress (Student)

### 2. Build and Submit Semester Plan (Student)

### 3. Review and Submit Feedback (Advisor)

## Use case diagram

![Use case diagram](diagrams/use-case.png)

### Phase 2 notes

- **Build and Submit Semester Plan** is independent of **View Degree Progress**; viewing progress is not a required sub-step.
- Students view their own degree progress and can view the status and feedback outcome for their plans.
- **Review and Submit Feedback** includes **View Pending Plans**, **View Selected Student Degree Progress**, and **Submit Feedback and Decision**; feedback and a decision are part of the advisor's review flow.
- Login is a precondition implied by the Student and Advisor actors, not a use case.

## Model diagram

![Model diagram](diagrams/model.png)

The editable Mermaid source is retained below. Phase 5 revisions are reflected
in the diagram and in the model notes.

```mermaid
erDiagram
  Student ||--o{ SemesterPlan : submits
  Advisor ||--o{ Student : advises
  Program ||--o{ Student : followed_by
  Program ||--o{ ProgramRequirement : requires
  Course ||--o{ ProgramRequirement : satisfies
  SemesterPlan ||--o{ SemesterPlanCourse : contains
  Course ||--o{ SemesterPlanCourse : listed_in
  Student ||--o{ StudentCourse : has_record
  Course ||--o{ StudentCourse : recorded_for
  GradeScale ||--o{ StudentCourse : grades
  Course ||--o{ CoursePrerequisite : requires
  Course ||--o{ CoursePrerequisite : prerequisite_for
  Advisor ||--o{ Feedback : writes
  SemesterPlan ||--o{ Feedback : reviewed_as

  Student {
    int student_id PK
    int program_id FK
    int advisor_id FK
    string name
    string email
    string status
  }

  Advisor {
    int advisor_id PK
    string name
    string email
  }

  Program {
    int program_id PK
    string name
    string degree_title
    int required_credits
    int max_credits
  }

  Course {
    int course_id PK
    string code
    string title
    int credits
    string faculty
    string department
  }

  ProgramRequirement {
    int pr_id PK
    int program_id FK
    int course_id FK
    string category
    bool required
    string note
  }

  SemesterPlan {
    int sp_id PK
    int student_id FK
    string semester
    date created_at
    date submitted_at
    string status
    string notes
  }

  SemesterPlanCourse {
    int spc_id PK
    int sp_id FK
    int course_id FK
  }

  Feedback {
    int feedback_id PK
    int sp_id FK
    int advisor_id FK
    date created_at
    string comment
    string decision
  }

  StudentCourse {
    int sc_id PK
    int student_id FK
    int course_id FK
    string grade FK
    string sem_completed
    string status
  }

  GradeScale {
    string grade PK
    float points
  }

  CoursePrerequisite {
    int cp_id PK
    int course_id FK
    int prereq_id FK
  }
```

### Phase 3 notes

- A `Student` follows one `Program` and is assigned one `Advisor`; an advisor can advise many students. The advisor's pending-plan queue is limited to plans belonging to their assigned students.
- `StudentCourse` records a student's course outcome, including grade, completion semester, and status. These records support both degree-progress calculations and prerequisite validation.
- `CoursePrerequisite` is a self-referential course association: a course can list multiple prerequisite courses, and passing any one listed prerequisite is sufficient for eligibility.
- A prerequisite counts as passed only when its `StudentCourse` status is completed and its `GradeScale.points` value is at least the points assigned to C.
- Each `SemesterPlan` represents one semester, so `semester` is stored on the plan and shared by all its `SemesterPlanCourse` entries. `SemesterPlanCourse` only links selected courses to a plan; course approval and priority are not tracked individually because review feedback applies to the plan overall.
- `SemesterPlanCourse` has a unique `(sp_id, course_id)` pair so one course cannot be added twice to the same plan; the same course may still appear in different semester plans.
- `ProgramRequirement` links the program requirements to courses and supports degree-progress checks.
- `Feedback` belongs to a reviewed semester plan and is written by an advisor; the student is derived through the plan, and `decision` records the advisor's overall outcome.
- `Program.max_credits` sets the maximum credits allowed in a student's semester plan.
- `SemesterPlan.status` is `Draft`, `Submitted`, `Approved`, or `Request Changes`.
- `Feedback.decision` is `Approve` or `Request changes`.
- Advisor review queue shows only `Submitted` plans for students assigned to the signed-in advisor, ordered oldest submission first; drafts and already-decided plans are excluded. The expanded review uses the existing plan/student/course/feedback entities and displays read-only degree progress including calculated GPA; no GPA column is stored.
- `StudentCourse.status` is `Completed` or `In progress`.
- Phase 5 GPA addition: `GradeScale` stores each UWI letter grade and quality-point value; `StudentCourse.grade` references `GradeScale.grade`. Dashboard GPA is credit-weighted and shows `N/A` when the student has no completed grade records.
- Phase 5 credit update: every catalog course is three credits. Degree progress and GPA use the course credit values, while semester-plan capacity uses `Program.max_credits` and rejects additions that would exceed it.

## Wireframes

Phase 4 review: the student-crafted wireframes cover the three named workflows for MyAdvisor and match the model decisions from earlier phases.

### Student Dashboard

![Student dashboard](wireframes/MyAdvisor_Student_Dashboard.png)

### Build Semester Plan

![Build semester plan](wireframes/MyAdvisor_Student_BuildPlan.png)

### Student My Plans

![Student my plans](wireframes/MyAdvisor_Student_MyPlans.png)

### Advisor Review Plans

![Advisor review plans](wireframes/MyAdvisor_Advisor_ReviewPlans.png)

`python manage.py report` also embeds any PNG/JPG still missing from `docs/wireframes/`.

## Theming

- Theme direction: Squilla Fund.
- Color system: teal blue (#388087), moonstone blue (#6FB3B8), powder blue (#BADFE7), Magic Mint (#C2EDCE), and White Smoke (#F6F6F2). Warning messages use a light-red background with dark-red text for clear distinction.
- Typography: the MyAdvisor wordmark uses Kaushan Script, a bold slanted brush script chosen to closely match the student wireframe; Fraunces display headings and Source Sans 3 body text remain for the rest of the interface.
- Applied across the landing, login, register, dashboard, Build Plan, My Plans, authenticated shell, session-expired page, admin shell, and server config page. Shared Bootstrap controls, tables, and alerts use the same palette; warnings/errors have a light-red background and dark-red text. The MyAdvisor wordmark remains in Kaushan Script.

## Implementation notes

- The student dashboard was restyled toward the wireframe’s horizontal header, degree/semester context row, three progress blocks (Credits earned, Core (incl. Foundation), Electives), and paired course panels. The overall degree card and GPA use course-credit weighting; Core and Electives cards count required courses from `ProgramRequirement` categories.
- Demo academic seed data uses 31 catalog courses at three credits each, for a 93-credit degree requirement. Requirements are 23 Core courses (including Foundation) and 8 Elective courses. Bob's 23 completed Core courses yield 69 / 93 credits earned and 23 / 23 Core (incl. Foundation); Electives are 0 / 8 courses.
- Replaced the dashboard's Semester Plan Snapshot with the wireframe's Eligible Next Semester panel. The listed choices come from the wireframe's course set and are filtered by prerequisite completion; COMP 2605 is excluded because it is already completed.
- Updated catalog display names: ACCT 1002 — Introduction to Financial Accounting; ACCT 1003 — Introduction to Cost and Management Accounting; COMP 1600 — Introduction to Computing Concepts; COMP 1601 — Computer Programming I; COMP 1602 — Computer Programming II.
- Updated catalog display names: COMP 1603 — Computer Programming III; COMP 2601 — Computer Architecture; COMP 2602 — Computer Networks; COMP 2603 — Object-Oriented Programming; COMP 2604 — Operating Systems.
- Updated catalog display names: COMP 2605 — Enterprise Database Systems; COMP 2606 — Software Engineering I; COMP 2611 — Data Structures; ECON 1001 — Introduction to Microeconomics; ECON 1002 — Introduction to Macroeconomics.
- Updated catalog display names: FOUN 1101 — Caribbean Civilisation; FOUN 1105 — Scientific and Technical Writing; FOUN 1301 — Law, Governance, Economy and Society; INFO 3609 — Internship I; MKTG 2001 — Principles of Marketing (replacing the incorrect MGMT 2001 code).
- Updated catalog display names: MGMT 2021 — Business Law I; MGMT 2008 — Organizational Behaviour; MGMT 2032 — Managerial Economics; MGMT 2012 — Quantitative Methods (replacing MGMT 2023); COMP 3603 — Human-Computer Interaction; COMP 3606 — Wireless and Mobile Computing; COMP 3613 — Software Engineering II.
- Added prerequisites: COMP 1602 requires COMP 1601; COMP 2611 requires COMP 1602; COMP 2605 requires COMP 1601; COMP 3606 requires COMP 2602; COMP 3613 requires COMP 2606. COMP 3605 retains its MATH 2250 prerequisite. Prerequisite checks require a completed C-or-better grade from `GradeScale`.
- Build Plan options now use the 26-course union of Bob's seeded completed-course list and his three originally planned courses. The options are grouped and alphabetized by course code in a bounded, independently scrollable list matching the wireframe; courses completed by the signed-in student show Completed and cannot be added again.
- Build Plan typography was reduced to match the dashboard scale: 1.1rem navigation, 1.25rem panel headings, and approximately 1rem course, summary, and action text.
- Final seeded roster is five students total including Bob: Bob, Ian McCarthy, Celeste Weston, Kate Baxter, and Nelly miller. The seed command and targeted `purge-demo-students` command remove Lee Benjamin, Rupert Welch, and Bridget Harvey with their associated student records, plans, plan-course rows, transcripts, feedback, and user accounts. Ian has no completed courses and displays all unfinished Year 1 courses as eligible next-semester options. Celeste and Nelly each have five completed Year 1 courses; their remaining Year 1 courses appear as eligible options. Kate has completed all ten listed Year 1 courses and has five Year 2 courses in her next-semester plan. Ian and Celeste have five year-one courses in their plans; Nelly has five year-two courses. There is no seeded year-three student after Rupert's removal. Each planned course is three credits.
- Kate's eligible-next-semester fallback now lists every catalog course whose numeric code is in the 2000s, and the eligible-course panels use a consistent vertical scrollbar for every student.
- Eligible Year 1 and Year 2 recommendations are both labeled `Core`, matching the program's course classification.
- Eligible course recommendations exclude any course already recorded as completed for the signed-in student, including Bob's completed 2000-level core courses.
- Students who have completed the full core sequence also receive the remaining advanced eligible courses, including COMP 3603, COMP 3606, and COMP 3613, subject to prerequisite checks.
- The advanced eligible set explicitly includes MGMT 2012; selecting that set depends only on completing the ten defined Year 1 courses, not on a separate requirement-count calculation.
- Build Plan now includes MGMT 2012 in its available catalog, so students can add it to a semester plan when it is not already completed and the plan has capacity.
- INFO 2605, MATH 2250, and MGMT 2012 are classified as Electives across the application; Year 1 and the remaining Year 2 course codes remain Core, while advanced elective recommendations display Elective.
- Student visual verification of this dashboard polish is pending.
- The student My Plans view uses the existing `SemesterPlan`, `SemesterPlanCourse`, `Course`, and `Feedback` entities. A thin authenticated route delegates to the plan service; repository queries return only the signed-in student's plans, with courses, credit totals, and feedback presented in a wireframe-style table with expandable details. Verification against the wireframe is pending.
- Advisor review dashboard follows the advisor wireframe's Pending Plans list and expanded read-only student progress, including GPA, planned courses, and feedback context. The queue is scoped to students assigned to the Advisor record linked to the signed-in admin. Verification against the wireframe is pending.
- Advisor list behavior: show only Submitted plans belonging to assigned students, oldest submission first; exclude drafts and decided plans. The expanded view shows the existing degree progress summaries and calculated GPA, with Plan Courses on the left and Feedback and Decision on the right, matching the wireframe. Completed transcript rows are not repeated in the advisor detail view. Decisions use `Feedback` and transition `SemesterPlan.status` to `Approved` or `Request Changes`.
- Advisor demo login is admin / adminpass. The seed data marks Nelly's year-two plan as Submitted for review; other new demo plans remain Draft.
- Student code-check evidence: the admin route constructs the repository/service and delegates to `get_admin_dashboard_view`; no query logic was placed in the router. The initial duplicate `Literal` field attempt was reconciled into one `Feedback.decision` field and a named SQL `CheckConstraint`, preserving the exact ERD decisions while keeping the SQLModel field type portable. Automated advisor service/template/model tests pass; visual workflow verification is pending.
- Dashboard progress correction: Core (incl. Foundation) and Electives display course counts (23 and 8 requirements), while Credits earned remains credit-based (69 / 93 for Bob). The catalog has 31 three-credit courses; the current database's ProgramRequirement rows were refreshed with `sync-degree-requirements` without resetting student plans or transcripts.

## Deployed app

Phase 6. Public Render URL (not localhost). Markers open this to mark the three workflows.

https://faststarter-ejhk.onrender.com

## Logins

Every account a marker needs, including extra users you added. Starter accounts:

- bob / bobpass — regular user
- ian / ianpass — regular user
- celeste / celestepass — regular user
- kate / katepass — regular user
- nelly / nellypass — regular user
- admin / adminpass — admin

## YouTube URL

https://youtu.be/msbEr-FdGUY

## GitHub repository

[EllieD27/uwi-comp3613a1-my-advisor](https://github.com/EllieD27/uwi-comp3613a1-my-advisor)

## Session transcripts

Filled when the Guide builds the report: the agent writes chat markdown into `docs/transcripts/`; `python manage.py report` packages them.

Guide packaged **6** chat(s) in `docs/transcripts/` (and `docs/transcripts.zip`).

Index: [docs/transcripts/INDEX.md](transcripts/INDEX.md)

- [`phase-1-project-and-workflows`](transcripts/phase-1-project-and-workflows.md)
- [`phase-2-use-case-design`](transcripts/phase-2-use-case-design.md)
- [`phase-3-model-design`](transcripts/phase-3-model-design.md)
- [`phase-4-wireframe-review`](transcripts/phase-4-wireframe-review.md)
- [`phase-5-continuation`](transcripts/phase-5-continuation.md)
- [`phase-6-deploy-and-report`](transcripts/phase-6-deploy-and-report.md)

## Competency (student-judge)

Filled by Guide from the student-judge run when this report was built.

**Judged at:** 2026-10-12T13:36:00-04:00
**Evidence pass:** fresh re-read of accessible native Copilot chats, current `docs/report.md`, all available phase evidence records, diagrams, wireframes, and deployment evidence; prior `docs/judge.md` ignored

**Student / session:** Eliana Dookhoo / MyAdvisor / COMP 3613A1
**Artifact:** Accessible Copilot Guide chats, six Guide-written/evidence transcript files, current report, UML/ERD artefacts, wireframes, and deployed app evidence
**Phases in evidence:** 1–6 (COMP 3613; Phase 5 polish, Phase 6 deploy)

## Totals

| | Count / value |
|--|--|
| Metrics on rubric | 12 (M1–M12) |
| N/A (excluded) | 0 |
| Metrics scored | 12 |
| Scoreable max | 48 |
| Awarded total | **44 / 48** |
| **Overall (avg of scored)** | **3.7 / 4** |
| Impression mark | **18 / 20** |

## Scorecard

| ID | Metric | Score / 4 | In avg | Evidence |
|----|--------|----------:|:------:|----------|
| M1 | Phase discipline | 4 | yes | The report contains the design artefacts before the implementation notes, Phase 5 includes multiple refinement passes, and Phase 6 deployment followed the local-workflow claim. |
| M2 | Problem framing | 4 | yes | The student-owned project, three `Feature (user)` workflows, use-case relationships, model rules, four wireframes, and branding decisions are all represented in the current report and phase evidence records. |
| M3 | Decision ownership | 4 | yes | The student made concrete domain decisions throughout Phase 5: Kate/Ian/Bob eligibility behavior, course classification, inclusion of advanced courses, and cross-application elective counts. |
| M4 | Artefact-before-code | 4 | yes | The UML PNG/JSON, Mermaid ERD, four wireframes, and implementation notes show that the build followed the assignment artefacts rather than replacing them with an unrelated design. |
| M5 | Verification habit | 3 | yes | The student stated that workflows worked locally, then continued reporting concrete mismatches and requested fixes. Deployment health, landing, and login behavior were also verified. A 4 is not awarded because the report does not preserve a detailed observation note for every screen. |
| M6 | Assignment fit | 4 | yes | The report documents FastStarter auth reuse, the layered routes/dependencies/schemas/services/repositories/models architecture, ERD-aligned workflows, theming, polish, and Render deployment. No inline-SQL route violation is evidenced. |
| M7 | Slice explanation | 3 | yes | The student explained domain behavior in their own words, for example “completed courses are shown in the eligible list” and “INFO 2605 is an elective,” then requested targeted cross-application corrections. The accessible record does not expose the earlier code-snippet exchanges, but the Guide did not establish a student refusal. |
| M8 | Prompt quality | 4 | yes | Prompts were concrete and testable: remove completed courses, add missing course codes, use a scrollbar, change “Year 2” to “Core,” and apply elective classification consistently. |
| M9 | Response to pushback | 4 | yes | The Phase 5 continuation shows sustained polish instead of accepting the first build: recommendation filtering, seeded student scenarios, labels, capacity/catalog behavior, and classification were revised across the application. |
| M10 | Integrity | 3 | yes | No paste-back, external-assist, suspicion, or edited-skill evidence was found; skill integrity is explicitly `pass`. The score reflects clean available evidence while acknowledging that earlier native chats are not accessible. |
| M11 | Provenance continuity | 3 | yes | The implementation and polish decisions remain consistent with MyAdvisor, the named workflows, model rules, wireframes, and seeded data. The unavailable native Phase 1–4 chats prevent a fully direct continuity trace, but the artefacts align. |
| M12 | Sincerity trajectory | 4 | yes | No suspicion round was entered, no sincerity blocks were required, and the accessible Phase 5 and Phase 6 turns show consistent student-owned correction requests through deployment. |

## Strengths

- All six COMP 3613 phases are represented: project/workflows, use cases, model, wireframes, theme/build/polish, and deployment.
- The student repeatedly found and corrected real workflow mismatches instead of stopping at the first successful build.
- The implementation stayed anchored to the MyAdvisor domain, wireframes, seeded users, course rules, and layered architecture.
- Deployment is complete and evidenced by the public URL and successful `/health` response.
- The report includes the required marker logins, diagrams, wireframes, implementation notes, transcripts package, and skill-integrity verification.

## Gaps (priority order)

1. The native Phase 1–4 chats are not available in the accessible project-session index. The report therefore uses clearly labeled artifact-based evidence records rather than fabricated dialogue.
2. The report could be stronger with brief student-observed screenshots or notes for each deployed workflow, but this is a documentation-strengthening opportunity, not a failed phase gate.

## Phase gate status

| Phase | Status | Note |
|-------|--------|------|
| 1 | met | MyAdvisor and three named workflows are recorded. |
| 2 | met | Use-case relationships, actor associations, and the UML PNG/JSON are present. |
| 3 | met | ERD entities, relationships, lifecycle rules, constraints, prerequisites, and grade rules are documented. |
| 4 | met | Four student-crafted wireframes are present and embedded in the report. |
| 5 | met | Theme, implementation, mismatch-driven refinement, model/data corrections, and local workflow completion are documented. |
| 6 | met | Public Render URL and marker logins are recorded; `/health` responds successfully. |

## Recommended next practice

- Add a short deployed verification note for each of the four main screens, recording the observed result and any final mismatch. This would make the already-complete Phase 5 evidence easier for a marker to audit.

## Integrity note

- **Clean on available evidence.** No external-assist/paste-back flag, suspicion spiral, or edited-skills finding was identified. Earlier native Phase 1–4 chats were unavailable, so their contents were not invented.

## Provenance flags

- Earlier native Phase 1–4 Guide chats unavailable to the report-building session.
- No edited-skills flag: `skill-integrity` is `pass`.
- No external-assist or transcript-gaming flag found.

## Sincerity log summary

- Blocks found: 0 | max round: 0 | min/mean/final confidence: not logged | trend: not applicable | cleared: yes

## Skips

- Skips: 0/3 used. No skip was recorded in the accessible Guide chats or current evidence records.

## Skill integrity

Course skills are hashed at export and compared to `.agents/skills.lock.json`. Do not edit `.agents/skills/`, `.cursor/skills/`, or `AGENTS.md`.

- Status: **pass**
- Root: `e84cd692d0b85eefe546385661958c27d07e8be6c5176a82012f68ccff5c8beb`
- none
