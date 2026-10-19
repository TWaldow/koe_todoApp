from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.auth import require_token
from app.db import get_db

router = APIRouter(prefix="/folders", tags=["folders"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[schemas.FolderRead])
def list_folders(db: Session = Depends(get_db)):
    """Alle Ordner, sortiert nach `position`."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("", response_model=schemas.FolderRead, status_code=status.HTTP_201_CREATED)
def create_folder(data: schemas.FolderCreate, db: Session = Depends(get_db)):
    """Ordner anlegen."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.patch("/{folder_id}", response_model=schemas.FolderRead)
def update_folder(folder_id: int, data: schemas.FolderUpdate, db: Session = Depends(get_db)):
    """Name, Farbe oder Position ändern."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(folder_id: int, db: Session = Depends(get_db)):
    """Ordner löschen. 409 bei "Allgemein" (is_system)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)