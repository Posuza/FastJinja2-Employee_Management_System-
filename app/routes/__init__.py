from fastapi import APIRouter
from app.routes.auth import router as auth_router
from app.routes.profile import router as profile_router
from app.routes.employees import router as employees_router
from app.routes.users import router as users_router  # Make sure this is included
from app.routes.error_handlers import router as error_router

# Create main router that includes all sub-routers
router = APIRouter()

# Include all route modules
router.include_router(auth_router)
router.include_router(profile_router)
router.include_router(employees_router)
router.include_router(users_router)  # Make sure this is included
router.include_router(error_router)