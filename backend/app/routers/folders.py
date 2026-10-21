from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError

from app import schemas
from app.auth import require_token
from app.database import get_db

from app.models import Folder, Todo



router = APIRouter(prefix="/folders", tags=["folders"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[schemas.FolderRead])
def list_folders(db: Session = Depends(get_db)):
    """Alle Ordner, sortiert nach `position`."""
    db_folders = db.execute(select(Folder).order_by(Folder.position)).scalars().all()
    if not db_folders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No folders found")
    return db_folders
    


@router.post("", response_model=schemas.FolderRead, status_code=status.HTTP_201_CREATED)
def create_folder(data: schemas.FolderCreate, db: Session = Depends(get_db)):
    """Ordner anlegen."""
    max_position = db.scalar(select(func.max(Folder.position)))
    if max_position is None:
        position = 0
    else:
        position = max_position + 1
    folder = Folder(name=data.name, color=data.color, position=position)
    db.add(folder)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Folder name already exists")
    db.refresh(folder)
    return folder


@router.patch("/{folder_id}", response_model=schemas.FolderRead)
def update_folder(folder_id: int, data: schemas.FolderUpdate, db: Session = Depends(get_db)):
    """Name, Farbe oder Position ändern."""
    folder = db.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(folder, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Folder name already exists")
    db.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(folder_id: int, db: Session = Depends(get_db)):
    """Ordner löschen. 409 bei "Allgemein" (is_system)."""
    folder = db.get(Folder, folder_id)
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    if folder.is_system:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="System folder cannot be deleted")

    general = db.scalar(select(Folder).where(Folder.is_system))
    db.execute(update(Todo).where(Todo.folder_id == folder_id).values(folder_id=general.id))
    db.delete(folder)
    db.commit()