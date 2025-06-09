from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date # For date query parameters

from .. import crud, models, schemas
from ..database import SessionLocal # Or from .auth import get_db
from ..routers.auth import get_current_active_user, get_db # Reusing get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.DataObject])
def list_data_objects(
    skip: int = 0,
    limit: int = 100,
    questionnaire_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    data_objects = crud.get_data_objects(
        db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        questionnaire_id=questionnaire_id,
        start_date=start_date,
        end_date=end_date
    )
    return data_objects

@router.get("/{data_object_id}", response_model=schemas.DataObject)
def read_data_object(
    data_object_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_data_object = crud.get_data_object(db, data_object_id=data_object_id)
    if db_data_object is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DataObject not found")

    # Verify ownership: check if the questionnaire linked to the data object belongs to the current user
    if db_data_object.questionnaire.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this DataObject")

    return db_data_object

@router.put("/{data_object_id}", response_model=schemas.DataObject)
def update_submitted_data_object(
    data_object_id: int,
    data_update: schemas.DataObjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    updated_object = crud.update_data_object(
        db=db,
        data_object_id=data_object_id,
        data_update=data_update,
        current_user=current_user
    )
    if updated_object is None:
        # This implies either not found or not owned, as crud function checks ownership
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DataObject not found or not authorized to update")
    return updated_object

@router.post("/merge/", response_model=schemas.DataObject, status_code=status.HTTP_201_CREATED)
def merge_multiple_data_objects(
    merge_request: schemas.DataObjectMergeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if len(merge_request.data_object_ids) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least two DataObject IDs must be provided for merging.")

    merged_data_object = crud.merge_data_objects(
        db=db,
        user=current_user,
        object_ids=merge_request.data_object_ids,
        target_questionnaire_id=merge_request.target_questionnaire_id,
        new_submitter_name=merge_request.new_submitter_name,
        new_additional_info=merge_request.new_additional_info,
        new_latitude=merge_request.new_latitude,
        new_longitude=merge_request.new_longitude
    )

    if merged_data_object is None:
        # This could be due to various reasons checked in crud:
        # - Target questionnaire not found or not owned.
        # - One or more source DataObjects not found or not owned.
        # - Fewer than 2 source objects actually found/valid.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to merge DataObjects. Ensure all source IDs are valid, owned by user, and target questionnaire is valid and owned by user.")

    return merged_data_object

@router.get("/nearby_suggestions/", response_model=List[schemas.DataObject])
def get_nearby_data_object_suggestions(
    source_data_object_id: int,
    distance_m: float = 500.0,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    try:
        nearby_objects = crud.get_nearby_data_objects(
            db=db,
            current_user=current_user,
            source_data_object_id=source_data_object_id,
            max_distance_meters=distance_m,
            skip=skip,
            limit=limit
        )
        return nearby_objects
    except ValueError as e:
        # Catch specific errors raised by CRUD function for bad input
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
