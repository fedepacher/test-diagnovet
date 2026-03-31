from enum import Enum


class AcceptedLanguages(str, Enum):
    """ doc """
    ES = "es"
    ES_ES = "es-ES"
    ES_MX = "es-MX"
    ES_AR = "es-AR"
    ES_CO = "es-CO"
    EN = "en"
    EN_US = "en-US"
    EN_GB = "en-GB"
    EN_AU = "en-AU"
    EN_CA = "en-CA"
    PT = "pt"
    PT_BR = "pt-BR"
    PT_PT = "pt-PT"
    DEFAULT = "es"


class StatusEnum(str, Enum):
    """Enumeration for general statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class ResultEnum(str, Enum):
    """Enumeration for operation results."""
    SUCCESS = "success"
    FAILURE = "failure"
