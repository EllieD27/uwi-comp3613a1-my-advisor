from app.database import get_cli_session
from app.repositories.academic import AcademicRepository
from app.services.semester_plan import SemesterPlanService
from app.models.user import User
from sqlmodel import select

with get_cli_session() as db:
    repo = AcademicRepository(db)
    service = SemesterPlanService(repo)
    user = db.exec(select(User).where(User.username == 'bob')).one()
    print('before', service.get_build_plan_view(user.id)['selected_codes'])
    print('added', service.add_course_to_plan(user.id, 'INFO 2605'))
    print('after', service.get_build_plan_view(user.id)['selected_codes'])
    print('submit', service.submit_plan(user.id))
    print('status', service.get_build_plan_view(user.id)['plan'].status)
