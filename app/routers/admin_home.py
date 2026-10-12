from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep, IsUserLoggedIn, get_current_user, is_admin
from . import router, templates
from app.repositories.academic import AcademicRepository
from app.services.advisor_review import AdvisorReviewService
from app.utilities.flash import flash

@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db:SessionDep
):
    repo = AcademicRepository(db)
    service = AdvisorReviewService(repo)
    dashboard_view = service.get_admin_dashboard_view(user.id)

    return templates.TemplateResponse(
        request=request, 
        name="admin.html",
        context={
            "user": user,
            "dashboard_view": dashboard_view,
        }
    )


@router.post("/admin/plans/{sp_id}/decision", name="admin_submit_plan_decision")
async def admin_submit_plan_decision(
    request: Request,
    user: AdminDep,
    db: SessionDep,
    sp_id: int,
):
    form = await request.form()
    decision = str(form.get("decision", ""))
    comment = str(form.get("comment", ""))

    service = AdvisorReviewService(AcademicRepository(db))
    if service.submit_plan_decision(user.id, sp_id, decision, comment):
        flash(request, "Plan decision and feedback submitted.", "success")
    else:
        flash(request, "This plan is no longer pending or the decision is invalid.", "danger")

    return RedirectResponse(url=request.url_for("admin_home_view"), status_code=303)
