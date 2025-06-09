from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# Association Table for User Favorites
user_favorite_data_objects = Table(
    'user_favorite_data_objects', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('data_object_id', Integer, ForeignKey('dataobjects.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    questionnaires = relationship("Questionnaire", back_populates="owner")
    favorite_data_objects = relationship(
        "DataObject",
        secondary=user_favorite_data_objects,
        back_populates="favorited_by_users"
    )

class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    password = Column(String, nullable=True) # For filling access
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="questionnaires")
    elements = relationship("QuestionElement", back_populates="questionnaire", cascade="all, delete-orphan")
    data_objects = relationship("DataObject", back_populates="questionnaire", cascade="all, delete-orphan")

class QuestionElement(Base):
    __tablename__ = "questionelements" # Changed from questionelements to questionelements

    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"))
    field_type = Column(String, nullable=False) # E.g., "text", "number", "coordinates_lat", "coordinates_lon", "date", "email"
    label = Column(String, nullable=False)
    options = Column(JSON, nullable=True) # For dropdowns, multiple choice, etc.

    questionnaire = relationship("Questionnaire", back_populates="elements")

class DataObject(Base):
    __tablename__ = "dataobjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"))
    submitter_name = Column(String, nullable=True) # Name of volunteer/association
    submission_date = Column(DateTime(timezone=True), server_default=func.now())
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    data_values = Column(JSON, nullable=False) # Stores answers to QuestionElements
    additional_info = Column(String, nullable=True) # Info added later

    questionnaire = relationship("Questionnaire", back_populates="data_objects")
    favorited_by_users = relationship(
        "User",
        secondary=user_favorite_data_objects,
        back_populates="favorite_data_objects"
    )
