from decimal import Decimal
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
class PagoRead(SQLModel):
    id: int
    pedido_id: int
    mp_payment_id: Optional[int] = None
    mp_status: str
    mp_status_detail: Optional[str] = None
    external_reference: str
    idempotency_key: str
    transaction_amount: Decimal
    payment_method_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


#====== Hecho por ia, ver si está bien

#Webhook de MercadoPago
#Según UML:
#topic=payment → sdk.payment().get(resource_id)
#Entonces el webhook mínimo:
class MercadoPagoWebhook(SQLModel):
    resource_id: Optional[str] = Field(
        default=None,
        description="ID del recurso informado por MercadoPago"
    )
    topic: Optional[str] = Field(
        default=None,
        description="Tipo de notificación. Ej: payment"
    )
