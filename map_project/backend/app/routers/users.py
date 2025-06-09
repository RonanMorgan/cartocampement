from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db # Import get_db from database.py
from .auth import get_current_active_user

router = APIRouter()

# Dependency to get a DB session (REMOVED - now imported)
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_name(db, name=user.name)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    created_user = crud.create_user(db=db, user=user)
    return created_user

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    # The user object from get_current_active_user might not have all relationships loaded by default.
    # Depending on how User schema is (e.g. if it expects favorite_data_objects to be populated),
    # we might need to refresh the user object from DB or ensure get_current_active_user does.
    # For now, assuming the current_user object is sufficient or User schema handles lazy loading.
    # To be safe, one might do: db_user = crud.get_user(db, current_user.id) and return db_user.
    # However, User schema now includes favorite_data_objects: List[DataObject] = []
    # SQLAlchemy lazy loading should handle this if accessed.
    return current_user

@router.post("/me/favorites/{data_object_id}", response_model=schemas.User)
def add_data_object_to_favorites(
    data_object_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    updated_user = crud.add_favorite(db=db, user_id=current_user.id, data_object_id=data_object_id)
    if not updated_user:
        raise HTTPException(status_code=404, detail="DataObject not found or not accessible to user")
    return updated_user # User schema should now show the updated favorites

@router.get("/me/favorites/", response_model=List[schemas.DataObject])
def get_my_favorites(
    db: Session = Depends(get_db), # Not strictly needed by crud.get_user_favorites if current_user has them
    current_user: models.User = Depends(get_current_active_user)
):
    # crud.get_user_favorites expects user_id, but current_user from Depends is already the model.
    # If current_user.favorite_data_objects is already populated by SQLAlchemy's lazy loading
    # upon User schema serialization, this can be direct.
    # Let's assume crud.get_user_favorites is the safer way if direct access isn't populated.
    return crud.get_user_favorites(db=db, user_id=current_user.id)


@router.delete("/me/favorites/{data_object_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_data_object_from_favorites(
    data_object_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    user = crud.remove_favorite(db=db, user_id=current_user.id, data_object_id=data_object_id)
    if not user:
        # This could mean data object wasn't found, or wasn't a favorite.
        # For DELETE, idempotency often means returning 204 even if it wasn't there.
        # However, if we want to be strict:
        raise HTTPException(status_code=404, detail="DataObject not found or not in user's favorites")
    return None
