from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "8above-api",
        "version": "0.1.0",
    }
