import logging
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.core.database import get_session
from app.modules.dominio_3.Pago.schemas import CrearPagoRequest, PagoCrearResponse, PagoEstadoResponse
from app.modules.dominio_3.Pago.service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pagos", tags=["pagos"])

def get_payment_service(session: Session = Depends(get_session)) -> PaymentService:
    return PaymentService(session)


# 1. Endpoint para crear el pago (La Ventanilla de Cobro)
@router.post("/crear", response_model=PagoCrearResponse, status_code=201)
def crear_pago(
    data: CrearPagoRequest,
    svc: PaymentService = Depends(get_payment_service),
):
    """
    Rúbrica: Crea pago. En nuestra implementación (Checkout PRO),
    genera la preferencia y devuelve el init_point para redirigir.
    """
    return svc.crear_pago(data.pedido_id)


# 2. Endpoint para escuchar a MercadoPago (La Puerta Trasera)
@router.post("/webhook", status_code=200)
async def webhook(
    request: Request,
    svc: PaymentService = Depends(get_payment_service),
):
    """
    Rúbrica: Endpoint IPN de MercadoPago. Actualiza estado del pago y del pedido.
    """
    try:
        query_params = dict(request.query_params)
        
        # MercadoPago a veces manda JSON y a veces Form-Data, hay que atajar los dos:
        if request.headers.get("content-type", "").startswith("application/json"):
            data = await request.json()
        else:
            data = dict(await request.form())
            
        return svc.procesar_webhook(data, query_params=query_params)
    except Exception as e:
        logger.exception("Error en webhook MP")
        return {"status": "error", "reason": str(e)}


# 3. Endpoint para consultar el estado (El Mostrador de Consultas)
@router.get("/{pedido_id}", response_model=PagoEstadoResponse)
def consultar_pago(
    pedido_id: int,
    svc: PaymentService = Depends(get_payment_service),
):
    """
    Rúbrica: Consulta el pago asociado a un pedido.
    """
    return svc.obtener_pago(pedido_id)
