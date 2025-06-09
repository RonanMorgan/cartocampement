from fastapi import APIRouter, Depends, HTTPException, status, Header # Added Header
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import SessionLocal
# Updated imports from .auth
from .auth import get_current_active_user, get_current_user_optional, get_db

router = APIRouter() # Ensure this line is present

# --- Questionnaire Endpoints ---

@router.post("/", response_model=schemas.Questionnaire, status_code=status.HTTP_201_CREATED)
def create_new_questionnaire(
    questionnaire: schemas.QuestionnaireCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    return crud.create_questionnaire(db=db, questionnaire=questionnaire, owner_id=current_user.id)

@router.get("/{questionnaire_id}", response_model=schemas.Questionnaire)
async def read_questionnaire_public( # Renamed for clarity, marked async
    questionnaire_id: int,
    db: Session = Depends(get_db),
    # Allow optional JWT authentication
    current_user: Optional[models.User] = Depends(get_current_user_optional),
    x_questionnaire_password: Optional[str] = Header(None, alias="X-Questionnaire-Password")
):
    db_questionnaire = crud.get_questionnaire(db, questionnaire_id=questionnaire_id)
    if db_questionnaire is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")

    # If the user is authenticated and is the owner, grant access
    if current_user and db_questionnaire.owner_id == current_user.id:
        return db_questionnaire

    # If the questionnaire has a password, it must be verified
    if db_questionnaire.password: # Assumes plaintext password as per subtask decision
        if x_questionnaire_password is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password required to view this questionnaire")
        if x_questionnaire_password != db_questionnaire.password:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password for this questionnaire")

    # If questionnaire has no password, or if correct password was provided, allow access
    # Also covers the case where owner is accessing (already returned)
    return db_questionnaire

@router.get("/", response_model=List[schemas.Questionnaire])
def read_user_questionnaires(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    questionnaires = crud.get_questionnaires_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return questionnaires

@router.put("/{questionnaire_id}", response_model=schemas.Questionnaire)
def update_existing_questionnaire(
    questionnaire_id: int,
    questionnaire_update: schemas.QuestionnaireUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_questionnaire = crud.get_questionnaire(db, questionnaire_id=questionnaire_id)
    if db_questionnaire is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")
    if db_questionnaire.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this questionnaire")
    return crud.update_questionnaire(db=db, questionnaire_id=questionnaire_id, questionnaire_update=questionnaire_update)

@router.delete("/{questionnaire_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_questionnaire(
    questionnaire_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_questionnaire = crud.get_questionnaire(db, questionnaire_id=questionnaire_id)
    if db_questionnaire is None:
        # Still return 204 if not found, as per idempotent delete, or 404 if preferred.
        # For now, let's be explicit if it existed and was owned, or not.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")
    if db_questionnaire.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this questionnaire")
    crud.delete_questionnaire(db=db, questionnaire_id=questionnaire_id)
    return None # FastAPI handles 204 No Content

# --- QuestionElement Endpoints ---

@router.post("/{questionnaire_id}/elements/", response_model=schemas.QuestionElement, status_code=status.HTTP_201_CREATED)
def create_new_element_for_questionnaire(
    questionnaire_id: int,
    element: schemas.QuestionElementCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_questionnaire = crud.get_questionnaire(db, questionnaire_id=questionnaire_id)
    if db_questionnaire is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")
    if db_questionnaire.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add elements to this questionnaire")
    return crud.create_questionnaire_element(db=db, element=element, questionnaire_id=questionnaire_id)

@router.put("/{questionnaire_id}/elements/{element_id}", response_model=schemas.QuestionElement)
def update_existing_element(
    questionnaire_id: int, # Used to verify ownership via questionnaire
    element_id: int,
    element_update: schemas.QuestionElementUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_questionnaire = crud.get_questionnaire(db, questionnaire_id=questionnaire_id)
    if db_questionnaire is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")
    if db_questionnaire.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify elements of this questionnaire")

    db_element = crud.get_questionnaire_element(db, element_id=element_id)
    if db_element is None or db_element.questionnaire_id != questionnaire_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QuestionElement not found or does not belong to this questionnaire")

    return crud.update_questionnaire_element(db=db, element_id=element_id, element_update=element_update)

@router.delete("/{questionnaire_id}/elements/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_element(
    questionnaire_id: int, # Used to verify ownership
    element_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_questionnaire = crud.get_questionnaire(db, questionnaire_id=questionnaire_id)
    if db_questionnaire is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")
    if db_questionnaire.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete elements from this questionnaire")

    db_element = crud.get_questionnaire_element(db, element_id=element_id)
    if db_element is None or db_element.questionnaire_id != questionnaire_id:
        # Idempotency: if element not found or not part of this questionnaire, can still return 204
        # However, for clarity, we can raise 404 if it's not found.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QuestionElement not found or does not belong to this questionnaire")

    crud.delete_questionnaire_element(db=db, element_id=element_id)
    return None


# --- Data Submission Endpoint ---

# from fastapi import Header # No longer needed here as it's imported at the top

@router.post("/{questionnaire_id}/submit", response_model=schemas.DataObject, status_code=status.HTTP_201_CREATED)
def submit_data_to_questionnaire(
    questionnaire_id: int,
    data: schemas.DataObjectCreate,
    db: Session = Depends(get_db),
    x_questionnaire_password: Optional[str] = Header(None, alias="X-Questionnaire-Password") # For questionnaire password
):
    db_questionnaire = crud.get_questionnaire(db, questionnaire_id=questionnaire_id)
    if db_questionnaire is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")

    # Password check for submission (if questionnaire has one)
    if db_questionnaire.password:
        if x_questionnaire_password is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password required for this questionnaire submission"
            )
        # Simple plain text comparison for now. In a real app, hash questionnaire passwords.
        if x_questionnaire_password != db_questionnaire.password:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Incorrect password for questionnaire submission"
            )

    # Basic validation: check if all keys in data_values correspond to actual question element labels or IDs
    # This is a simplified validation. A more robust one would check types, options, etc.
    # For now, we just ensure the keys are plausible.
    # Example: Collect all element labels/ids for validation
    # valid_element_keys = {el.label for el in db_questionnaire.elements} | {str(el.id) for el in db_questionnaire.elements}
    # for key in data.data_values.keys():
    #     if key not in valid_element_keys:
    #         raise HTTPException(status_code=400, detail=f"Invalid data key: {key}")

    return crud.create_data_object(db=db, data=data, questionnaire_id=questionnaire_id)
