from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.lesion import router as lesion_router

router = APIRouter(prefix="/api")

# Team members: add your feature's router here, e.g.
# from app.api.routes.<feature> import router as <feature>_router
# router.include_router(<feature>_router)
router.include_router(auth_router)
router.include_router(lesion_router)
