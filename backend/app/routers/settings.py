from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import require_token
from app.db import get_db

router = APIRouter(
    prefix="/settings", tags=["settings"], dependencies=[Depends(require_token)]
)


@router.get("", response_model=schemas.SettingsRead)
def read_settings(db: Session = Depends(get_db)):
    """Server-Settings lesen (Zeitzone, Reset-Stunde)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.patch("", response_model=schemas.SettingsRead)
def update_settings(data: schemas.SettingsUpdate, db: Session = Depends(get_db)):
    """Server-Settings ändern."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)