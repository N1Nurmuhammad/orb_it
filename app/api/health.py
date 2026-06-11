"""Health/meta endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Lightweight liveness probe used by orchestration and humans.",
)
async def health() -> dict:
    return {"ok": True}
