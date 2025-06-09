from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# --- QuestionElement Schemas ---
class QuestionElementBase(BaseModel):
    field_type: str
    label: str
    options: Optional[Dict[str, Any]] = None

class QuestionElementCreate(QuestionElementBase):
    pass

class QuestionElementUpdate(BaseModel):
    field_type: Optional[str] = None
    label: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class QuestionElement(QuestionElementBase):
    id: int
    questionnaire_id: int
    model_config = ConfigDict(from_attributes=True)


# --- DataObject Schemas ---
class DataObjectBase(BaseModel): # Ensuring this is the version used
    submitter_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    data_values: Dict[str, Any]
    additional_info: Optional[str] = None # Critical: Ensure this is part of DataObjectBase

class DataObjectCreate(DataObjectBase):
    pass

class DataObjectUpdate(BaseModel):
    additional_info: Optional[str] = None

class DataObjectMergeRequest(BaseModel):
    data_object_ids: List[int]
    target_questionnaire_id: int
    new_submitter_name: Optional[str] = None
    new_additional_info: Optional[str] = None
    new_latitude: Optional[float] = None
    new_longitude: Optional[float] = None

class DataObject(DataObjectBase):
    id: int
    questionnaire_id: int
    submission_date: datetime
    # additional_info is inherited from DataObjectBase
    model_config = ConfigDict(from_attributes=True)


# --- Questionnaire Schemas ---
class QuestionnaireBase(BaseModel):
    title: str
    description: Optional[str] = None
    password: Optional[str] = None

class QuestionnaireCreate(QuestionnaireBase):
    elements: List[QuestionElementCreate] = []

class QuestionnaireUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    password: Optional[str] = None

class Questionnaire(QuestionnaireBase):
    id: int
    owner_id: int
    elements: List[QuestionElement] = []
    data_objects: List[DataObject] = []
    model_config = ConfigDict(from_attributes=True)


# --- User Schemas ---
class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    questionnaires: List[Questionnaire] = []
    favorite_data_objects: List[DataObject] = []
    model_config = ConfigDict(from_attributes=True)
