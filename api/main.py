import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.app.router.breed_router import router as breed_router
from api.app.router.country_router import router as country_router
from api.app.router.gender_router import router as gender_router
from api.app.router.institution_router import router as institution_router
from api.app.router.patient_router import router as patient_router
from api.app.router.profile_router import router as profile_router
from api.app.router.role_router import router as role_router
from api.app.router.specie_router import router as specie_router
from api.app.router.study_router import router as study_router
from api.app.router.user_router import router as user_router
from api.app.utils.lifespan import lifespan
from api.app.utils.middlewares import DBSessionMiddleware, LanguageMiddleware
from api.app.utils.db import handler_db
from api.app.utils.settings import Settings


logging.info("Starting database handler")
handler_db()

logging.info("Starting FastAPI server")

# Initialize the FastAPI app
app = FastAPI(lifespan=lifespan)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(DBSessionMiddleware)
app.add_middleware(LanguageMiddleware)

# Mount static files
os.makedirs(Settings.upload_dir, exist_ok=True)
app.mount(
    "/static",
    StaticFiles(directory=Settings.upload_dir),
    name="static"
)

# Include API routers

app.include_router(breed_router)
app.include_router(country_router)
app.include_router(gender_router)
app.include_router(institution_router)
app.include_router(patient_router)
app.include_router(profile_router)
app.include_router(role_router)
app.include_router(specie_router)
app.include_router(study_router)
app.include_router(user_router)

"""
Notes:
- `lifespan`: Manages the application lifecycle events, like starting and shutting down.
- `CORSMiddleware`: Enables Cross-Origin Resource Sharing for the API.
    Replace `["*"]` with specific domains in production.
- Each router (e.g., `user`) should be properly defined in its respective module and
    organized with prefixes and tags for better documentation.
"""
