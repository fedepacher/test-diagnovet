"""
Settings module for managing application environment variables.

This module retrieves and provides access to environment variables
used for database configuration, email settings, and application secrets.
"""

import logging
import json
import os


class Settings:
    """
    Handles configuration using environment variables.
    """

    run_env = os.getenv('RUN_ENV')

    _db_name: str = os.getenv('DB_NAME')
    _db_user: str = os.getenv('DB_USER')
    db_pass: str = os.getenv('DB_PASS')
    db_host: str = os.getenv('DB_HOST')
    db_port: int = os.getenv('DB_PORT')

    log_file: str | None = os.getenv('LOG_FILE', None)

    secret_key: str = os.getenv('SECRET_KEY')
    token_expire: int = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
    deployment_service: str = os.getenv('DEPLOYMENT_SERVICE')

    cors_origins_env = os.getenv("CORS_ORIGINS")

    cors_origins: list[str] = ([origin.strip() for origin in cors_origins_env.split(",")] if cors_origins_env else [])
    upload_dir: str = os.getenv('UPLOAD_DIR')

    llm_provider: str = os.getenv('LLM_PROVIDER')
    openai_api_key: str = os.getenv('OPENAI_API_KEY')
    openai_model: str = os.getenv('OPENAI_MODEL', "gpt-4o-mini")
    gemini_api_key: str = os.getenv('GEMINI_API_KEY')
    gemini_model: str = os.getenv('GEMINI_MODEL', "gemini-2.0-flash")

    use_ai_filter = os.getenv("IMAGE_AI_FILTER", "false")

    @classmethod
    def db_name(cls):
        """
        Retrieves the database name, appending a test suffix if in test environment.

        Returns:
            str: The database name, with '_test' suffix if RUN_ENV is 'test'.
        """
        return cls._db_name + '_' + cls.run_env

    @classmethod
    def db_user(cls):
        """
        Retrieves the database user.

        Returns:
            str: The database user.
        """
        return cls._db_user
