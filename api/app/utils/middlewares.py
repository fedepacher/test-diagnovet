""" Middlewares """

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from api.app.utils.global_def import AcceptedLanguages

from api.app.utils.db import db


class DBSessionMiddleware(BaseHTTPMiddleware):
    """ doc """
    async def dispatch(self, request, call_next):
        if db.is_closed():
            db.connect()
        try:
            response = await call_next(request)
        finally:
            if not db.is_closed():
                db.close()
        return response


class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        raw_language = request.headers.get("accept-language", AcceptedLanguages.DEFAULT)
        accept_language = raw_language.split("-")[0]
        # Validate language
        if accept_language not in AcceptedLanguages.__members__.values():
            accept_language = AcceptedLanguages.DEFAULT  # Default to Spanish if invalid

        # Attach language to request state
        request.state.accept_language = accept_language

        # Process the request and add the Content-Language header
        response = await call_next(request)
        response.headers["Content-Language"] = accept_language
        return response
