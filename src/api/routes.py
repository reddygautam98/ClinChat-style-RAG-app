from fastapi import APIRouter
from .chat import router as chat_router
from .documents import router as documents_router


router = APIRouter()

router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(documents_router, prefix="/documents", tags=["documents"])