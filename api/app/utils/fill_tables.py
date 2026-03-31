import logging
from peewee import IntegrityError, ModelBase

from api.app.model.breed_model import Breeds
from api.app.model.country_model import Countries
from api.app.model.gender_model import Genders
from api.app.model.role_model import Roles
from api.app.model.specie_model import Species


def fill_table(table: ModelBase, table_content):
    """
    Fills table {table} with table {table_content}.

    :param table: Class name
    :param table_content: content of the table
    """
    logging.info(f"fill_table(table: {table}, table_content)")

    try:
        # Check if the table contains at least one element
        if table.select().exists():
            logging.info(f"The table {table.__name__} already contains data. Skipping table filling.")
            return
    except Exception as e:
        logging.error(f"Error checking if table {table.__name__} contains data: {e}")

    # Get the list of fields (column names) for the table
    table_fields = set(table._meta.fields.keys())

    for content in table_content:
        try:
            # Filter content to include only valid table fields
            valid_data = {k: v for k, v in content.items() if k in table_fields}

            # Create new record (auto id)
            table.create(**valid_data)
            logging.info(f"Inserted {content} into {table.__name__} table.")
        except IntegrityError:
            logging.error(f"Error while inserting/updating {content} in {table.__name__} table.")
        except Exception as e:
            logging.error(f"Unexpected error while inserting {content} into {table.__name__}: {e}")


def fill_country_table():
    data = [
        {"name": "germany", "spanish_name": "Alemania", "english_name": "Germany", "portuguese_name": "Alemanha"},
        {"name": "argentina", "spanish_name": "Argentina", "english_name": "Argentina",
         "portuguese_name": "Argentina"},
        {"name": "australia", "spanish_name": "Australia", "english_name": "Australia",
         "portuguese_name": "Austrália"},
        {"name": "brazil", "spanish_name": "Brasil", "english_name": "Brazil", "portuguese_name": "Brasil"},
        {"name": "china", "spanish_name": "China", "english_name": "China", "portuguese_name": "China"},
        {"name": "colombia", "spanish_name": "Colombia", "english_name": "Colombia",
         "portuguese_name": "Colômbia"},
        {"name": "spain", "spanish_name": "España", "english_name": "Spain", "portuguese_name": "Espanha"},
        {"name": "united states", "spanish_name": "Estados Unidos", "english_name": "United States",
         "portuguese_name": "Estados Unidos"},
    ]

    fill_table(Countries, data)


def fill_gender_table():
    data = [
        {"name": "male", "spanish_name": "Masculino", "english_name": "Male", "portuguese_name": "Masculino"},
        {"name": "female", "spanish_name": "Femenino", "english_name": "Female", "portuguese_name": "Feminino"}
    ]
    fill_table(Genders, data)


def fill_roles_table():
    data = [
        {
            "name": "owner",
            "spanish_name": "Propietario",
            "english_name": "Owner",
            "portuguese_name": "Proprietário",
            "description": "Pet owner responsible for the animal"
        },
        {
            "name": "veterinarian",
            "spanish_name": "Veterinario",
            "english_name": "Veterinarian",
            "portuguese_name": "Veterinário",
            "description": "Medical professional responsible for diagnosis and treatment"
        },
        {
            "name": "veterinary_assistant",
            "spanish_name": "Asistente Veterinario",
            "english_name": "Veterinary Assistant",
            "portuguese_name": "Assistente Veterinário",
            "description": "Supports veterinarians in clinical tasks"
        },
        {
            "name": "lab_technician",
            "spanish_name": "Técnico de Laboratorio",
            "english_name": "Lab Technician",
            "portuguese_name": "Técnico de Laboratório",
            "description": "Processes lab tests and diagnostic samples"
        },
        {
            "name": "radiologist",
            "spanish_name": "Radiólogo",
            "english_name": "Radiologist",
            "portuguese_name": "Radiologista",
            "description": "Specialist in imaging studies (X-ray, ultrasound, etc.)"
        },
        {
            "name": "clinic_admin",
            "spanish_name": "Administrador de Clínica",
            "english_name": "Clinic Administrator",
            "portuguese_name": "Administrador de Clínica",
            "description": "Manages clinic operations and staff"
        },
        {
            "name": "receptionist",
            "spanish_name": "Recepcionista",
            "english_name": "Receptionist",
            "portuguese_name": "Recepcionista",
            "description": "Handles appointments and client communication"
        },
        {
            "name": "system_admin",
            "spanish_name": "Administrador del Sistema",
            "english_name": "System Administrator",
            "portuguese_name": "Administrador do Sistema",
            "description": "Manages platform-level configuration and access"
        },
        {
            "name": "researcher",
            "spanish_name": "Investigador",
            "english_name": "Researcher",
            "portuguese_name": "Pesquisador",
            "description": "Analyzes veterinary data for research purposes"
        },
        {
            "name": "external_consultant",
            "spanish_name": "Consultor Externo",
            "english_name": "External Consultant",
            "portuguese_name": "Consultor Externo",
            "description": "External specialist providing second opinions"
        }
    ]
    fill_table(Roles, data)


def fill_species_table():
    data = [
        {
            "name": "dog",
            "spanish_name": "Perro",
            "english_name": "Dog",
            "portuguese_name": "Cão"
        },
        {
            "name": "cat",
            "spanish_name": "Gato",
            "english_name": "Cat",
            "portuguese_name": "Gato"
        }
    ]

    fill_table(Species, data)


def fill_breeds_table():
    dog_data = [
        {"name": "mixed", "spanish_name": "Mestizo", "english_name": "Mixed Breed", "portuguese_name": "SRD"},
        {"name": "labrador_retriever", "spanish_name": "Labrador Retriever", "english_name": "Labrador Retriever",
         "portuguese_name": "Labrador Retriever"},
        {"name": "german_shepherd", "spanish_name": "Pastor Alemán", "english_name": "German Shepherd",
         "portuguese_name": "Pastor Alemão"},
        {"name": "bulldog", "spanish_name": "Bulldog", "english_name": "Bulldog", "portuguese_name": "Bulldog"},
        {"name": "poodle", "spanish_name": "Caniche", "english_name": "Poodle", "portuguese_name": "Poodle"},
        {"name": "chihuahua", "spanish_name": "Chihuahua", "english_name": "Chihuahua", "portuguese_name": "Chihuahua"},
        {"name": "beagle", "spanish_name": "Beagle", "english_name": "Beagle", "portuguese_name": "Beagle"},
        {"name": "boxer", "spanish_name": "Bóxer", "english_name": "Boxer", "portuguese_name": "Boxer"},
        {"name": "dachshund", "spanish_name": "Salchicha", "english_name": "Dachshund", "portuguese_name": "Dachshund"},
        {"name": "rottweiler", "spanish_name": "Rottweiler", "english_name": "Rottweiler",
         "portuguese_name": "Rottweiler"},
        {"name": "yorkshire_terrier", "spanish_name": "Yorkshire Terrier", "english_name": "Yorkshire Terrier",
         "portuguese_name": "Yorkshire Terrier"},
        {"name": "golden_retriever", "spanish_name": "Golden Retriever", "english_name": "Golden Retriever",
         "portuguese_name": "Golden Retriever"},
        {"name": "schnauzer", "spanish_name": "Schnauzer", "english_name": "Schnauzer", "portuguese_name": "Schnauzer"},
        {"name": "border_collie", "spanish_name": "Border Collie", "english_name": "Border Collie",
         "portuguese_name": "Border Collie"},
    ]

    cat_data = [
        {"name": "mixed", "spanish_name": "Mestizo", "english_name": "Mixed Breed", "portuguese_name": "SRD"},
        {"name": "persian", "spanish_name": "Persa", "english_name": "Persian", "portuguese_name": "Persa"},
        {"name": "siamese", "spanish_name": "Siamés", "english_name": "Siamese", "portuguese_name": "Siamês"},
        {"name": "maine_coon", "spanish_name": "Maine Coon", "english_name": "Maine Coon",
         "portuguese_name": "Maine Coon"},
        {"name": "british_shorthair", "spanish_name": "Británico de Pelo Corto", "english_name": "British Shorthair",
         "portuguese_name": "British Shorthair"},
        {"name": "ragdoll", "spanish_name": "Ragdoll", "english_name": "Ragdoll", "portuguese_name": "Ragdoll"},
        {"name": "bengal", "spanish_name": "Bengalí", "english_name": "Bengal", "portuguese_name": "Bengal"},
        {"name": "sphynx", "spanish_name": "Esfinge", "english_name": "Sphynx", "portuguese_name": "Sphynx"},
    ]

    dog = Species.get(Species.name == "dog")
    cat = Species.get(Species.name == "cat")

    data = []

    for breed in dog_data:
        data.append({**breed, "species": dog.id})

    for breed in cat_data:
        data.append({**breed, "species": cat.id})

    fill_table(Breeds, data)


def fill_all_tables():
    fill_country_table()
    fill_gender_table()
    fill_roles_table()
    fill_species_table()
    fill_breeds_table()
