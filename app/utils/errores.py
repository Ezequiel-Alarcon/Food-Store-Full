from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

async def manejar_validaciones(request: Request, exc: RequestValidationError):
    #TODO : Deuda técnica - Los headers CORS (`Access-Control-Allow-Origin: *`) se están seteando manualmente en cada exception handler en lugar de delegarlo al middleware CORSMiddleware. Esto es frágil y propenso a inconsistencias.
    detalles = exc.errors()
    primer_error = detalles[0]

    mensaje = f"Error de validación en el campo: {primer_error['loc'][-1]} - {primer_error['msg']}"
    return JSONResponse(
        status_code=422,
        content={"mensaje": mensaje, "codigo": 422},
        headers={"Access-Control-Allow-Origin": "*"}
    )

async def manejar_http_exceptions(request: Request, exc: HTTPException):
    #TODO : Deuda técnica - Mismo problema que arriba: CORS seteado manualmente en vez de depender del middleware.
    return JSONResponse(
        status_code=exc.status_code,
        content={"mensaje": exc.detail, "codigo": exc.status_code},
        headers={"Access-Control-Allow-Origin": "*"}
    )