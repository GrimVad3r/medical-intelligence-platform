"""HTTP exception handlers."""

from fastapi import HTTPException

def not_found(message: str = "Not found") -> HTTPException:
    return HTTPException(status_code=404, detail=message)


def bad_request(message: str = "Bad request") -> HTTPException:
    return HTTPException(status_code=400, detail=message)
