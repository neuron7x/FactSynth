"""Application entrypoint with registered error handlers."""

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from .app import create_app
from .core.errors import (
    http_exception_handler,
    unexpected_exception_handler,
    validation_exception_handler,
)

app = create_app(register_handlers=False)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unexpected_exception_handler)
