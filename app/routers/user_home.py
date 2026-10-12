from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.academic import AcademicRepository
from app.services.degree_progress import DegreeProgressService
from app.services.semester_plan import SemesterPlanService
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    repo = AcademicRepository(db)
    service = DegreeProgressService(repo)
    progress = service.get_student_progress(user.id)
    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "progress": progress,
        },
    )


@router.get("/app/build-plan", response_class=HTMLResponse, name="student_build_plan_view")
async def build_plan_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    repo = AcademicRepository(db)
    service = SemesterPlanService(repo)
    plan_view = service.get_build_plan_view(user.id)
    return templates.TemplateResponse(
        request=request,
        name="build_plan.html",
        context={
            "user": user,
            "plan": plan_view,
        },
    )


@router.post("/app/build-plan", name="student_build_plan_submit")
async def build_plan_action(request: Request, user: AuthDep, db: SessionDep):
    form = await request.form()
    action = form.get("action")
    code = form.get("course_code")

    repo = AcademicRepository(db)
    service = SemesterPlanService(repo)

    if action == "add" and code:
        service.add_course_to_plan(user.id, code)
    elif action == "remove" and code:
        service.remove_course_from_plan(user.id, code)
    elif action == "submit":
        service.submit_plan(user.id)

    return RedirectResponse(url="/app/build-plan", status_code=303)


@router.get("/app/my-plans", response_class=HTMLResponse, name="student_my_plans_view")
async def my_plans_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    repo = AcademicRepository(db)
    service = SemesterPlanService(repo)
    my_plans_view = service.get_my_plans_view(user.id)
    return templates.TemplateResponse(
        request=request,
        name="my_plans.html",
        context={
            "user": user,
            "my_plans": my_plans_view,
        },
    )


@router.get("/app/gpa", name="student_gpa_view")
async def student_gpa_view(user: AuthDep, db: SessionDep):
    repo = AcademicRepository(db)
    service = DegreeProgressService(repo)
    gpa = service.get_student_gpa(user.id)
    return {"gpa": gpa}
    
