import fitz
import logging
import os
import pdfplumber
from fastapi import HTTPException, status, UploadFile
from datetime import datetime
from uuid import uuid4
from peewee import fn
from typing import Type

from api.app.model.base_model import BaseModel
from api.app.model.breed_model import Breeds as BreedsModel
from api.app.model.country_model import Countries as CountryModel
from api.app.model.gender_model import Genders as GenderModel
from api.app.model.role_model import Roles as RolesModel
from api.app.model.specie_model import Species as SpeciesModel
from api.app.utils.settings import Settings


def check_if_id_exist(element_id, table_name):
    """
    Checks whether a specific ID exists in the given database table.

    This function queries the specified table to verify if a record with the
    provided ID exists. If not, it logs an error and raises an HTTP 404 exception.

    Args:
        element_id (int): The ID of the record to check.
        table_name: The database table object (e.g., a Peewee model) where the check is performed.

    Raises:
        HTTPException: If the record does not exist, raises a 404 Not Found error with a descriptive message.
    """
    if not table_name.select().where(table_name.id == element_id).exists():
        msg = f"{table_name.__name__} ID {element_id} does not exist"
        logging.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg
        )


def get_language_fields(accept_language: str):
    """Map language to corresponding field names."""
    logging.info(f"get_language_fields(accept_language: {accept_language})")
    models = {
        "breed": BreedsModel,
        "country": CountryModel,
        "gender": GenderModel,
        "role": RolesModel,
        "specie": SpeciesModel,
    }

    # Language suffix map
    suffixes = {
        "en": "english_name",
        "es": "spanish_name",
        "pt": "portuguese_name",
    }

    # Build the dictionary dynamically
    language_fields = {
        lang: {
            key: getattr(model, attr)
            for key, model in models.items()
        }
        for lang, attr in suffixes.items()
    }
    language = language_fields.get(accept_language, language_fields["es"])
    logging.info(f"Language selected {language}")
    return language


def get_generic_list(name: str, model, schema, accept_language):
    logging.info(f"get_generic_list(name: {name}, "
                 f"model: {model}, "
                 f"schema: {schema}, "
                 f"accept_language: {accept_language})")
    language_fields = get_language_fields(accept_language)

    try:
        alias = f'{name}_name'
        query = model.select(model.id, language_fields[name].alias(alias)).order_by(language_fields[name].asc())
        results = list(query)  # Execute the query and fetch results
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {name} found."
            )

        elements_list = []
        for record in results:
            element = schema(
                id=record.id,
                name=getattr(record, alias)
            )
            elements_list.append(element)

        return elements_list
    except HTTPException as e:
        logging.error(f"HTTPException occurred while fetching {name}: {str(e)}")
        raise e  # Re-raise the HTTPException if triggered
    except Exception as e:
        logging.error(f"Error occurred while fetching {name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


def save_file(file: UploadFile, institution_id: int) -> str:
    path = f"{Settings.upload_dir}/documents/institution_{institution_id}"
    os.makedirs(path, exist_ok=True)

    file_extension = file.filename.split(".")[-1]
    unique_name = f"{datetime.now().timestamp()}_{uuid4().hex}.{file_extension}"

    file_path = os.path.join(path, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return file_path


def extract_text_from_pdf(file_path: str) -> str:
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text


def normalize_species(text: str | None) -> str | None:
    if not text:
        return None

    text = text.lower().strip()

    mapping = {
        "dog": ["dog", "canine", "canino", "perro"],
        "cat": ["cat", "feline", "felino", "gato"]
    }

    for canonical, variants in mapping.items():
        if any(v in text for v in variants):
            return canonical

    return text.replace(" ", "_")


def normalize_breed(text: str | None) -> str | None:
    if not text:
        return None

    text = text.lower().strip()

    mapping = {
        "mixed": ["mestizo", "criollo", "sin raza", "mixed"],
        "schnauzer": ["schnauzer", "schnauzer mini", "mini schnauzer", "schnauzer miniatura"],
        "labrador_retriever": ["labrador", "labrador retriever"],
        "german_shepherd": ["pastor aleman", "german shepherd"],
        "poodle": ["caniche", "poodle"],
        "bulldog": ["bulldog"],
        "chihuahua": ["chihuahua"],
        "beagle": ["beagle"],
        "boxer": ["boxer", "bóxer"],
        "dachshund": ["salchicha", "dachshund"],
        "rottweiler": ["rottweiler"],
        "yorkshire_terrier": ["yorkshire", "yorkshire terrier"],
        "golden_retriever": ["golden", "golden retriever"],
        "border_collie": ["border collie"]
    }

    for canonical, variants in mapping.items():
        if any(v in text for v in variants):
            return canonical

    return text.replace(" ", "_")


def parse_gender(text: str | None):
    if not text:
        return None, None

    text = text.lower().strip()

    # Gender
    if any(word in text for word in ["macho", "male"]):
        gender = "male"
    elif any(word in text for word in ["hembra", "female"]):
        gender = "female"
    else:
        gender = None

    # Neutered
    is_neutered = any(word in text for word in [
        "castrado",
        "esterilizado",
        "neutered",
        "spayed"
    ])

    return gender, is_neutered


def get_model_id(data: str | None, model: Type[BaseModel]) -> int | None:
    if not data:
        return None

    data = data.strip().lower()

    # Detect which fields exist in the model
    fields = []
    for field_name in ["name", "spanish_name", "english_name", "portuguese_name"]:
        if hasattr(model, field_name):
            fields.append(getattr(model, field_name))

    if not fields:
        return None

    # Build OR condition dynamically
    condition = None
    for field in fields:
        expr = fn.LOWER(field) == data
        condition = expr if condition is None else (condition | expr)

    obj = (
        model
        .select(model.id)
        .where(condition)
        .get_or_none()
    )

    return obj.id if obj else None


def get_language_attr(accept_language: str) -> str:
    suffixes = {
        "en": "english_name",
        "es": "spanish_name",
        "pt": "portuguese_name",
    }
    return suffixes.get(accept_language, "spanish_name")


def translate(instance, attr: str) -> str | None:
    if not instance:
        return None
    return getattr(instance, attr, None) or instance.name
