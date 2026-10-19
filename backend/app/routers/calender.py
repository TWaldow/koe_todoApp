from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_token

router = APIRouter(
    prefix="/calendar", tags=["calendar"], dependencies=[Depends(require_token)]
)


@router.post("/events")
def create_event():
    """Stub für feste Termine. Bleibt bis zum Kalender-Feature bei 501."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)