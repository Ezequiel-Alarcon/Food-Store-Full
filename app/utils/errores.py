from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

async def manejar_validaciones(request: Request, exc: RequestValidationError):
    detalles = exc.errors()
    primer_error = detalles[0]

    mensaje = f"Error de validación en el campo: {primer_error['loc'][-1]} - {primer_error['msg']}"
    return JSONResponse(
        status_code=422,
        content={"mensaje": mensaje, "codigo": 422}
    )

async def manejar_http_exceptions(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"mensaje": exc.detail, "codigo": exc.status_code}
    )