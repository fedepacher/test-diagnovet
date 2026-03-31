from pydantic import BaseModel


class PaginationInfo(BaseModel):
    total: int
    totalPages: int
    currentPage: int
    limit: int
