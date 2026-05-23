from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel
class HistorialEstadoPedidoRead(SQLModel):
    estado_desde: Optional[str] = None
    estado_hacia: str
    created_at: datetime