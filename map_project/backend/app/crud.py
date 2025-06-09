from sqlalchemy.orm import Session
from sqlalchemy import and_ # For combining filters
from . import models, schemas, utils # Added utils import
from .security import get_password_hash
from datetime import date, datetime
from typing import Optional, List, Tuple, Any, Dict # Added Tuple, Any, Dict
from sqlalchemy.exc import IntegrityError # For handling favorite already exists
import json # For data_values merge logic

# --- User CRUD operations ---
def get_user_by_name(db: Session, name: str) -> models.User | None:
    return db.query(models.User).filter(models.User.name == name).first()

def get_user(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(name=user.name, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


# --- Questionnaire CRUD operations ---
def create_questionnaire(db: Session, questionnaire: schemas.QuestionnaireCreate, owner_id: int) -> models.Questionnaire:
    # Separate elements from questionnaire data
    elements_data = questionnaire.elements
    questionnaire_data = questionnaire.model_dump(exclude={"elements"})

    db_questionnaire = models.Questionnaire(**questionnaire_data, owner_id=owner_id)
    db.add(db_questionnaire)
    db.commit() # Commit to get db_questionnaire.id

    for element_data in elements_data:
        create_questionnaire_element(db, element_data, questionnaire_id=db_questionnaire.id)

    db.refresh(db_questionnaire)
    return db_questionnaire

def get_questionnaire(db: Session, questionnaire_id: int) -> models.Questionnaire | None:
    return db.query(models.Questionnaire).filter(models.Questionnaire.id == questionnaire_id).first()

def get_questionnaires_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[models.Questionnaire]:
    return db.query(models.Questionnaire).filter(models.Questionnaire.owner_id == owner_id).offset(skip).limit(limit).all()

def update_questionnaire(db: Session, questionnaire_id: int, questionnaire_update: schemas.QuestionnaireUpdate) -> models.Questionnaire | None:
    db_questionnaire = get_questionnaire(db, questionnaire_id)
    if db_questionnaire:
        update_data = questionnaire_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_questionnaire, key, value)
        db.commit()
        db.refresh(db_questionnaire)
    return db_questionnaire

def delete_questionnaire(db: Session, questionnaire_id: int) -> models.Questionnaire | None:
    db_questionnaire = get_questionnaire(db, questionnaire_id)
    if db_questionnaire:
        db.delete(db_questionnaire)
        db.commit()
    return db_questionnaire


# --- QuestionElement CRUD operations ---
def create_questionnaire_element(db: Session, element: schemas.QuestionElementCreate, questionnaire_id: int) -> models.QuestionElement:
    db_element = models.QuestionElement(**element.model_dump(), questionnaire_id=questionnaire_id)
    db.add(db_element)
    db.commit()
    db.refresh(db_element)
    return db_element

def get_questionnaire_element(db: Session, element_id: int) -> models.QuestionElement | None:
    return db.query(models.QuestionElement).filter(models.QuestionElement.id == element_id).first()

def update_questionnaire_element(db: Session, element_id: int, element_update: schemas.QuestionElementUpdate) -> models.QuestionElement | None:
    db_element = get_questionnaire_element(db, element_id)
    if db_element:
        update_data = element_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_element, key, value)
        db.commit()
        db.refresh(db_element)
    return db_element

def delete_questionnaire_element(db: Session, element_id: int) -> models.QuestionElement | None:
    db_element = get_questionnaire_element(db, element_id)
    if db_element:
        db.delete(db_element)
        db.commit()
    return db_element


# --- DataObject CRUD operations ---
def create_data_object(db: Session, data: schemas.DataObjectCreate, questionnaire_id: int) -> models.DataObject:
    db_data_object = models.DataObject(**data.model_dump(), questionnaire_id=questionnaire_id)
    db.add(db_data_object)
    db.commit()
    db.refresh(db_data_object)
    return db_data_object


# --- Nearby DataObjects ---
def get_nearby_data_objects(
    db: Session,
    current_user: models.User,
    source_data_object_id: int,
    max_distance_meters: float,
    skip: int = 0,
    limit: int = 100
) -> List[models.DataObject]:

    # Get source object and verify ownership and coordinates
    source_do = db.query(models.DataObject)\
        .join(models.Questionnaire)\
        .filter(models.DataObject.id == source_data_object_id)\
        .filter(models.Questionnaire.owner_id == current_user.id)\
        .first()

    if not source_do:
        raise ValueError("Source DataObject not found or not owned by user.")
    if source_do.latitude is None or source_do.longitude is None:
        raise ValueError("Source DataObject does not have valid coordinates.")

    # Get all other data objects owned by the user with valid coordinates
    potential_matches = db.query(models.DataObject)\
        .join(models.Questionnaire)\
        .filter(models.Questionnaire.owner_id == current_user.id)\
        .filter(models.DataObject.id != source_data_object_id)\
        .filter(models.DataObject.latitude.isnot(None))\
        .filter(models.DataObject.longitude.isnot(None))\
        .all() # Fetch all to filter in Python; for large DBs, use geospatial queries

    nearby_objects = []
    for candidate_do in potential_matches:
        distance = utils.haversine_distance(
            source_do.latitude, source_do.longitude,
            candidate_do.latitude, candidate_do.longitude
        )
        if distance <= max_distance_meters:
            nearby_objects.append(candidate_do)

    # Apply pagination to the Python list of nearby objects
    return nearby_objects[skip : skip + limit]


# --- User Favorites CRUD operations ---
def add_favorite(db: Session, user_id: int, data_object_id: int) -> models.User | None:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    data_object = db.query(models.DataObject).join(models.Questionnaire)\
        .filter(models.DataObject.id == data_object_id)\
        .filter(models.Questionnaire.owner_id == user_id)\
        .first() # Ensure user can only favorite their own questionnaire's data

    if user and data_object:
        # Check if already favorited to prevent duplicate entries if DB doesn't handle it
        if data_object not in user.favorite_data_objects:
            user.favorite_data_objects.append(data_object)
            try:
                db.commit()
                db.refresh(user)
            except IntegrityError: # Should not happen if check above is done, but as fallback
                db.rollback()
                # Already favorited, or other integrity issue
        return user
    return None # User or (valid/owned) DataObject not found

def remove_favorite(db: Session, user_id: int, data_object_id: int) -> models.User | None:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    data_object = db.query(models.DataObject).filter(models.DataObject.id == data_object_id).first()

    if user and data_object and data_object in user.favorite_data_objects:
        user.favorite_data_objects.remove(data_object)
        db.commit()
        db.refresh(user)
        return user
    return None # User not found, or DataObject not found/not a favorite

def get_user_favorites(db: Session, user_id: int) -> List[models.DataObject]:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        return user.favorite_data_objects
    return []


# --- DataObject Merge Operation ---
def merge_data_objects(
    db: Session,
    user: models.User,
    object_ids: List[int],
    target_questionnaire_id: int,
    new_submitter_name: Optional[str] = None,
    new_additional_info: Optional[str] = None,
    new_latitude: Optional[float] = None,
    new_longitude: Optional[float] = None
) -> models.DataObject | None:
    if not object_ids or len(object_ids) < 2:
        # Need at least two objects to merge
        return None

    # Verify target questionnaire belongs to the user
    target_questionnaire = db.query(models.Questionnaire)\
        .filter(models.Questionnaire.id == target_questionnaire_id)\
        .filter(models.Questionnaire.owner_id == user.id)\
        .first()
    if not target_questionnaire:
        return None # Target questionnaire not found or not owned by user

    # Fetch and verify all source DataObjects belong to the user
    source_objects: List[models.DataObject] = []
    for obj_id in object_ids:
        obj = db.query(models.DataObject).join(models.Questionnaire)\
            .filter(models.DataObject.id == obj_id)\
            .filter(models.Questionnaire.owner_id == user.id)\
            .first()
        if not obj:
            return None # One of the source objects not found or not owned
        source_objects.append(obj)

    if not source_objects: # Should be caught by len < 2, but as safeguard
        return None

    # --- Simplified Merge Logic ---
    merged_data_values: Dict[str, Any] = {}
    all_keys = set()
    for obj in source_objects:
        all_keys.update(obj.data_values.keys())

    for key in all_keys:
        values = [obj.data_values.get(key) for obj in source_objects if obj.data_values.get(key) is not None]
        if not values:
            continue

        # Attempt to determine type for merging (simplified)
        first_value = values[0]
        if isinstance(first_value, (int, float)):
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if numeric_values:
                merged_data_values[key] = sum(numeric_values) / len(numeric_values)
        elif isinstance(first_value, str):
            merged_data_values[key] = " | ".join(str(v) for v in values)
        else: # list, dict, bool, etc. - take first or stringify
            merged_data_values[key] = values[0]


    # Coordinates
    final_latitude = new_latitude
    final_longitude = new_longitude
    if final_latitude is None or final_longitude is None: # One is None, try to calculate average
        lats = [obj.latitude for obj in source_objects if obj.latitude is not None]
        lons = [obj.longitude for obj in source_objects if obj.longitude is not None]
        if lats and lons: # Ensure we have some coordinates to average
             if final_latitude is None: final_latitude = sum(lats) / len(lats) if lats else None
             if final_longitude is None: final_longitude = sum(lons) / len(lons) if lons else None
        elif lats and final_latitude is None: # Only lats available
            final_latitude = sum(lats) / len(lats)
        elif lons and final_longitude is None: # Only lons available
            final_longitude = sum(lons) / len(lons)
        # If no source coordinates and no new_coordinates, they remain None


    # Submitter name and additional info
    final_submitter_name = new_submitter_name if new_submitter_name is not None else f"Merged by {user.name}"

    source_ids_str = ", ".join(map(str, object_ids))
    final_additional_info = new_additional_info if new_additional_info is not None else f"Merged from DataObjects: [{source_ids_str}]"
    if new_additional_info and "%IDS%" in new_additional_info: # Allow placeholder for IDs
        final_additional_info = new_additional_info.replace("%IDS%", source_ids_str)


    merged_do_schema = schemas.DataObjectCreate(
        submitter_name=final_submitter_name,
        latitude=final_latitude,
        longitude=final_longitude,
        data_values=merged_data_values, # This is already a dict
        additional_info=final_additional_info
    )

    # Create new DataObject
    # The create_data_object function expects a schema object.
    return create_data_object(db=db, data=merged_do_schema, questionnaire_id=target_questionnaire_id)

def get_data_object(db: Session, data_object_id: int) -> models.DataObject | None:
    return db.query(models.DataObject).filter(models.DataObject.id == data_object_id).first()

def get_data_objects(
    db: Session,
    current_user: models.User,
    skip: int = 0,
    limit: int = 100,
    questionnaire_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[models.DataObject]:
    query = db.query(models.DataObject).join(models.Questionnaire).filter(models.Questionnaire.owner_id == current_user.id)

    if questionnaire_id:
        query = query.filter(models.DataObject.questionnaire_id == questionnaire_id)
    if start_date:
        query = query.filter(models.DataObject.submission_date >= start_date)
    if end_date:
        # To make end_date inclusive, typically you'd query for < (end_date + 1 day)
        # For simplicity with date objects, we'll assume submission_date is just a date (though it's DateTime)
        # If submission_date is DateTime, ensure comparison is correct or cast column to date.
        # For now, using direct comparison. Consider time part if submission_date is DateTime.
        query = query.filter(models.DataObject.submission_date <= end_date)

    return query.offset(skip).limit(limit).all()

def update_data_object(
    db: Session,
    data_object_id: int,
    data_update: schemas.DataObjectUpdate,
    current_user: models.User
) -> models.DataObject | None:
    db_data_object = db.query(models.DataObject).join(models.Questionnaire)\
        .filter(models.DataObject.id == data_object_id)\
        .filter(models.Questionnaire.owner_id == current_user.id)\
        .first()

    if db_data_object:
        # Only additional_info is updatable for now as per DataObjectUpdate schema
        if data_update.additional_info is not None: # Check if it was provided
            db_data_object.additional_info = data_update.additional_info
        # If other fields were in DataObjectUpdate, update them similarly:
        # update_data = data_update.model_dump(exclude_unset=True)
        # for key, value in update_data.items():
        #     setattr(db_data_object, key, value)
        db.commit()
        db.refresh(db_data_object)
    return db_data_object
