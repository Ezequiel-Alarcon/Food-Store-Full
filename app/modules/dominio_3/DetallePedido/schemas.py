from app.modules.dominio_3.DetallePedido.models import DetallePedido
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlmodel import SQLModel, Field

class DetallePedidoCreate(SQLModel):
    producto_id: int = Field(..., description="ID del producto")
    cantidad: int = Field(..., gt=1, description="Cantidad del producto")
    personalizacion: Optional[List[int]] = Field(default=None, description="ID de la personalización")

class DetallePedidoRead(DetallePedido):
    pedido_id: int
    producto_id: int

    cantidad: int

    nombre_snapshot: str
    precio_snapshot: Decimal
    subtotal_snapshot: Decimal
    
    personalizacion: Optional[List[int]] = None
    created_ad: datetime

class DetallePedidoUpdate(SQLModel):
    cantidad: Optional[int] = Field(default=None, gt=1)
    personalizacion: Optional[List[int]] = None