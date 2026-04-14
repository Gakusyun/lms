from fastapi import APIRouter
from app.api.v1 import auth, students, teachers, reviewers, courses, leaves, status, student_courses, statistics, backup, schools, roles, audit_logs, notifications

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, tags=["authentication"])
api_router.include_router(students.router, tags=["students"])
api_router.include_router(teachers.router, tags=["teachers"])
api_router.include_router(reviewers.router, tags=["reviewers"])
api_router.include_router(courses.router, tags=["courses"])
api_router.include_router(leaves.router, tags=["leaves"])
api_router.include_router(schools.router, tags=["schools"])
api_router.include_router(roles.router, tags=["roles"])
api_router.include_router(status.router, tags=["status"])
api_router.include_router(student_courses.router, tags=["student-courses"])
api_router.include_router(statistics.router, tags=["statistics"])
api_router.include_router(backup.router, tags=["backup"])
api_router.include_router(audit_logs.router, tags=["audit-logs"])
api_router.include_router(notifications.router, tags=["notifications"])
