from fastapi import FastAPI
from .database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from . import models # Import models to ensure they are registered with Base

# Create database tables
# In a production app, you might want to use Alembic for migrations
models.Base.metadata.create_all(bind=engine)

from .routers import auth, users, questionnaires, data # Added data router

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app = FastAPI(title="Map Project API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Autorise le frontend
    allow_credentials=True,
    allow_methods=["*"],              # GET, POST, etc.
    allow_headers=["*"],              # Autorise tous les headers
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(questionnaires.router, prefix="/questionnaires", tags=["Questionnaires"])
app.include_router(data.router, prefix="/data", tags=["Data Objects"])


@app.get("/ping", tags=["Health Check"])
async def ping():
    return {"ping": "pong"}
